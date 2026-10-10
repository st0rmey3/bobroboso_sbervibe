"""Document processing, called only from the worker. Every stage is persisted, so the UI shows honest progress:
preprocessing → recognizing (OCR, optional) → extracting (LLM) → validating → done | needs_review | unreadable."""

import logging
import time

from sqlalchemy.orm import Session

from app import storage
from app.extraction import doctypes, preprocess, prompts
from app.llm import get_ocr, get_provider
from app.models import Document, DocumentStatus

log = logging.getLogger(__name__)

CONFIDENCE_REVIEW_THRESHOLD = 0.6
_MISSING = "Обязательное поле не найдено"


def _stage(session: Session, doc: Document, status: DocumentStatus) -> None:
    doc.status = status
    session.commit()
    log.info("document %s: stage %s", doc.id, status.value)


def _finish(session: Session, doc: Document, status: DocumentStatus, reason: str | None, t0: float) -> None:
    doc.status, doc.status_reason = status, reason
    doc.processing_ms = int((time.monotonic() - t0) * 1000)
    session.commit()
    log.info("document %s → %s (%s) in %d ms", doc.id, status.value, doc.detected_type, doc.processing_ms)


def process_document(session: Session, doc: Document) -> None:
    """Raises LLMError for the worker to retry. Sets a final status otherwise."""
    t0 = time.monotonic()
    doc.status_reason = None
    _stage(session, doc, DocumentStatus.preprocessing)
    try:
        pages = preprocess.load(storage.read(doc.storage_key), doc.mime)
    except preprocess.UnreadableFile as e:
        return _finish(session, doc, DocumentStatus.unreadable, str(e), t0)

    text, images = pages.text, pages.images
    ocr = get_ocr()
    if ocr is not None:
        _stage(session, doc, DocumentStatus.recognizing)
        page_texts = []
        for img in pages.images:
            page_texts.append(ocr.read_page(img))
        text = "\n\n".join(t for t in [pages.text, *page_texts] if t.strip())
        images = []  # the LLM works on recognized text only
        doc.ocr_text = text
        if not text.strip():
            return _finish(session, doc, DocumentStatus.unreadable, "На изображении не найден текст", t0)

    _stage(session, doc, DocumentStatus.extracting)
    llm = get_provider()
    cls = llm.complete_json(
        system=prompts.SYSTEM,
        prompt=prompts.classify_prompt(text),
        schema=doctypes.classification_schema(),
        images=images,
    )
    doc.llm_meta = {"provider": cls.provider, "model": cls.model, "ocr": ocr.name if ocr else None}
    if cls.data.get("readable") is False:
        reason = (cls.data.get("reason") or "Документ не читается").rstrip(". ")
        return _finish(session, doc, DocumentStatus.unreadable, f"{reason}. Загрузите более чёткое фото.", t0)
    detected = cls.data.get("doc_type")
    if detected not in doctypes.DOC_TYPES:
        doc.detected_type = doctypes.UNKNOWN
        reason = (cls.data.get("reason") or "Это не один из принимаемых документов").rstrip(". ")
        return _finish(session, doc, DocumentStatus.unreadable, f"{reason}. Загрузите нужный документ.", t0)

    dt = doctypes.DOC_TYPES[detected]
    doc.detected_type = dt.code
    ext = llm.complete_json(
        system=prompts.SYSTEM,
        prompt=prompts.extract_prompt(dt, text),
        schema=doctypes.extraction_schema(dt),
        images=images,
    )

    _stage(session, doc, DocumentStatus.validating)
    fields = doctypes.validate(dt, doctypes.fields_from(ext.data))
    doctypes.check_grounded(dt, fields, text)  # values must come from the file, not from the model's imagination
    doc.fields = fields
    labels = {f.name: f.label for f in dt.fields}
    reasons = []
    if doc.declared_type and doc.declared_type != dt.code:
        declared = doctypes.DOC_TYPES[doc.declared_type].label
        reasons.append(f"Загружен как «{declared}», а распознан как «{dt.label}»")
    # minimum fields are checked on the whole document (front + back), see applications.doc_slots
    problems = [f"{labels[n]}: {i}" for n, f in fields.items() for i in f["issues"] if i != _MISSING]
    if problems:
        reasons.append("; ".join(problems))
    unsure = [labels[n] for n, f in fields.items() if f["value"] and f["confidence"] < CONFIDENCE_REVIEW_THRESHOLD]
    if unsure:
        reasons.append("Перепроверьте: " + ", ".join(unsure))
    status = DocumentStatus.needs_review if reasons else DocumentStatus.done
    _finish(session, doc, status, ". ".join(reasons) or None, t0)
