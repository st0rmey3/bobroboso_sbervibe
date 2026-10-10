"""Application-level rules shared by API and worker."""

from sqlalchemy.orm import Session

from app.extraction.doctypes import DOC_TYPES, missing_required
from app.models import Application, ApplicationStatus, AuditEvent, DocumentStatus

_USABLE = {DocumentStatus.done, DocumentStatus.needs_review}
_IN_PROGRESS = {
    DocumentStatus.queued,
    DocumentStatus.preprocessing,
    DocumentStatus.recognizing,
    DocumentStatus.extracting,
    DocumentStatus.validating,
}


_ATTENTION = {DocumentStatus.unreadable, DocumentStatus.failed}


def _type_of(doc) -> str | None:
    return doc.detected_type if doc.detected_type in DOC_TYPES else doc.declared_type


def doc_slots(app: Application) -> list[dict]:
    """One entry per document type: its files (e.g. front + back) and fields merged across them.

    For each field the most reliable value wins: operator edit first, then the highest model confidence.
    The case's minimum-field check is done here, on the merged document, not per file.
    """
    extra = sorted({t for d in app.documents if (t := _type_of(d)) in DOC_TYPES and t not in app.doc_set})
    slots = []
    for code in [*app.doc_set, *extra]:
        dt = DOC_TYPES[code]
        files = [d for d in app.documents if _type_of(d) == code]
        parsed = [d for d in files if d.status in _USABLE]
        merged = {}
        for spec in dt.fields:
            candidates = [
                {**d.fields[spec.name], "document_id": d.id}
                for d in parsed
                if (d.fields or {}).get(spec.name, {}).get("value")
            ]
            best = max(candidates, key=lambda c: (bool(c.get("edited_by")), c["confidence"]), default=None)
            if best is None:
                best = {"value": None, "confidence": 0.0, "issues": [], "document_id": None}
            values = {c["value"] for c in candidates}
            if len(values) > 1 and not best.get("edited_by"):
                best = {**best, "issues": [*best["issues"], "В файлах разные значения: " + " / ".join(sorted(values))]}
            merged[spec.name] = best
        missing = missing_required(dt, merged) if parsed else []
        warnings = _duplicate_warnings(parsed)
        has_issues = any(f["issues"] for f in merged.values())
        if not files:
            state = "missing"
        elif any(d.status in _IN_PROGRESS for d in files):
            state = "processing"
        elif not parsed or missing or has_issues or warnings or any(d.status in _ATTENTION for d in files):
            state = "problem"
        else:
            state = "ok"
        slots.append(
            {
                "doc_type": code,
                "label": dt.label,
                "required": code in app.doc_set,
                "state": state,
                "document_ids": [d.id for d in files],
                "fields": merged,
                "missing_fields": missing,
                "warnings": warnings,
            }
        )
    return slots


_IDENTITY_FIELDS = ("series", "number")


def _duplicate_warnings(parsed: list) -> list[str]:
    """Same document uploaded twice as different files (re-saved photo, copy): same series+number."""
    seen: dict[tuple, str] = {}
    warnings = []
    for d in parsed:
        key = tuple((d.fields or {}).get(f, {}).get("value") for f in _IDENTITY_FIELDS)
        if not any(key):
            continue
        if key in seen:
            number = " ".join(v for v in key if v)
            warnings.append(f"Файлы «{seen[key]}» и «{d.filename}» — один и тот же документ (№ {number})")
        else:
            seen[key] = d.filename
    return warnings


def missing_types(app: Application) -> list[str]:
    """Doc types from the required set that have no usable document yet (bonus: ask applicant to upload)."""
    have = {_type_of(d) for d in app.documents if d.status in _USABLE | _IN_PROGRESS}
    return [code for code in app.doc_set if code not in have]


def refresh_status(app: Application) -> None:
    if app.status in (ApplicationStatus.accepted, ApplicationStatus.rejected):
        return
    statuses = {d.status for d in app.documents}
    if not statuses:
        app.status = ApplicationStatus.draft
    elif statuses & _IN_PROGRESS:
        app.status = ApplicationStatus.processing
    elif statuses - {DocumentStatus.done} or missing_types(app):
        app.status = ApplicationStatus.needs_review
    else:
        app.status = ApplicationStatus.ready


def audit(session: Session, app_id: str, actor: str, action: str, document_id: str | None = None, **data) -> None:
    session.add(AuditEvent(application_id=app_id, document_id=document_id, actor=actor, action=action, data=data))
