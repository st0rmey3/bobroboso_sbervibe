"""Document processing, called only from the worker. Stages are persisted so the UI shows honest progress."""

import logging
import time
from collections.abc import Callable

from sqlalchemy.orm import Session

from app import storage
from app.extraction import doctypes, preprocess, prompts
from app.llm import get_provider
from app.models import Document, DocumentStatus

log = logging.getLogger(__name__)

CONFIDENCE_REVIEW_THRESHOLD = 0.6


def _stage(session: Session, doc: Document, status: DocumentStatus, heartbeat: Callable[[], None]) -> None:
    doc.status = status
    session.commit()
    heartbeat()


def process_document(session: Session, doc: Document, heartbeat: Callable[[], None]) -> None:
    """Raises LLMError for the worker to retry. Sets a final status otherwise."""
    t0 = time.monotonic()
    _stage(session, doc, DocumentStatus.preprocessing, heartbeat)
    try:
        pages = preprocess.load(storage.read(doc.storage_key), doc.mime)
    except preprocess.UnreadableFile as e:
        doc.status, doc.status_reason = DocumentStatus.unreadable, str(e)
        session.commit()
        return

    _stage(session, doc, DocumentStatus.extracting, heartbeat)
    llm = get_provider()
    cls = llm.complete_json(
        system=prompts.SYSTEM,
        prompt=prompts.classify_prompt(pages.text),
        schema=doctypes.classification_schema(),
        images=pages.images,
    )
    heartbeat()
    detected = cls.data.get("doc_type")
    doc.llm_meta = {"provider": cls.provider, "model": cls.model, "classify_ms": cls.latency_ms}
    if not cls.data.get("readable", True):
        doc.status = DocumentStatus.unreadable
        doc.status_reason = cls.data.get("reason") or "Документ не читается: переснимите его чётче"
        doc.processing_ms = int((time.monotonic() - t0) * 1000)
        session.commit()
        return
    if detected not in doctypes.DOC_TYPES:
        doc.detected_type = doctypes.UNKNOWN
        doc.status = DocumentStatus.needs_review
        doc.status_reason = "Не удалось определить тип документа"
        doc.processing_ms = int((time.monotonic() - t0) * 1000)
        session.commit()
        return

    dt = doctypes.DOC_TYPES[detected]
    doc.detected_type = dt.code
    ext = llm.complete_json(
        system=prompts.SYSTEM,
        prompt=prompts.extract_prompt(dt, pages.text),
        schema=doctypes.extraction_schema(dt),
        images=pages.images,
    )
    doc.llm_meta = {**doc.llm_meta, "extract_ms": ext.latency_ms}

    _stage(session, doc, DocumentStatus.validating, heartbeat)
    fields = doctypes.validate(dt, ext.data.get("fields") or {})
    doc.fields = fields
    reasons = []
    if doc.declared_type and doc.declared_type != dt.code:
        reasons.append(f"Загружен как «{doc.declared_type}», распознан как «{dt.label}»")
    if any(f["issues"] or f["confidence"] < CONFIDENCE_REVIEW_THRESHOLD for f in fields.values()):
        reasons.append("Есть поля, которые стоит перепроверить")
    doc.status = DocumentStatus.needs_review if reasons else DocumentStatus.done
    doc.status_reason = "; ".join(reasons) or None
    doc.processing_ms = int((time.monotonic() - t0) * 1000)
    session.commit()
    log.info("document %s → %s (%s) in %d ms", doc.id, doc.status.value, dt.code, doc.processing_ms)
