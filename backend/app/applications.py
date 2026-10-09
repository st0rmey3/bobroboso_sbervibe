"""Application-level rules shared by API and worker."""

from sqlalchemy.orm import Session

from app.models import Application, ApplicationStatus, AuditEvent, DocumentStatus

_USABLE = {DocumentStatus.done, DocumentStatus.needs_review}
_IN_PROGRESS = {
    DocumentStatus.queued,
    DocumentStatus.preprocessing,
    DocumentStatus.extracting,
    DocumentStatus.validating,
}


def missing_types(app: Application) -> list[str]:
    """Doc types from the required set that have no usable document yet (bonus: ask applicant to upload)."""
    have = {d.detected_type or d.declared_type for d in app.documents if d.status in _USABLE | _IN_PROGRESS}
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
