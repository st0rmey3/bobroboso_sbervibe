"""Operator API. Every route requires a Keycloak token with role `operator` (router-level dependency)."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import storage
from app.applications import audit, missing_types, refresh_status
from app.auth import Operator, require_operator
from app.db import get_session
from app.jobs import queue
from app.models import Application, ApplicationStatus, AuditEvent, Document, DocumentStatus, Job, JobStatus
from app.schemas import (
    ApplicationListItem,
    ApplicationOperator,
    AuditEventOut,
    DocumentOperator,
    FieldsUpdate,
    Me,
    ProcessingItem,
    QueueStats,
)

IN_PROGRESS = [
    DocumentStatus.queued,
    DocumentStatus.preprocessing,
    DocumentStatus.recognizing,
    DocumentStatus.extracting,
    DocumentStatus.validating,
]
ATTENTION = {DocumentStatus.needs_review, DocumentStatus.unreadable, DocumentStatus.failed}

router = APIRouter(prefix="/api/operator", tags=["operator"], dependencies=[Depends(require_operator)])


def _doc(session: Session, doc_id: str) -> Document:
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Документ не найден")
    return doc


@router.get("/me", response_model=Me)
def me(op: Operator = Depends(require_operator)) -> Me:
    return Me(username=op.username, roles=op.roles)


@router.get("/applications", response_model=list[ApplicationListItem])
def list_applications(
    status: ApplicationStatus | None = None,
    country: str | None = None,
    q: str | None = None,
    session: Session = Depends(get_session),
) -> list[ApplicationListItem]:
    stmt = select(Application).order_by(Application.updated_at.desc())
    if status:
        stmt = stmt.where(Application.status == status)
    if country:
        stmt = stmt.where(Application.country == country)
    if q:
        stmt = stmt.where(Application.full_name.ilike(f"%{q.strip()}%"))
    return [
        ApplicationListItem(
            id=a.id,
            status=a.status,
            full_name=a.full_name,
            country=a.country,
            created_at=a.created_at,
            updated_at=a.updated_at,
            documents_total=len(a.documents),
            documents_done=sum(d.status == DocumentStatus.done for d in a.documents),
            documents_attention=sum(d.status in ATTENTION for d in a.documents),
        )
        for a in session.scalars(stmt)
    ]


@router.get("/applications/{app_id}", response_model=ApplicationOperator)
def get_application(app_id: str, session: Session = Depends(get_session)) -> ApplicationOperator:
    app = session.get(Application, app_id)
    if app is None:
        raise HTTPException(404, "Заявка не найдена")
    history = session.scalars(
        select(AuditEvent).where(AuditEvent.application_id == app_id).order_by(AuditEvent.created_at)
    )
    return ApplicationOperator(
        id=app.id,
        status=app.status,
        full_name=app.full_name,
        phone=app.phone,
        country=app.country,
        doc_set=app.doc_set,
        created_at=app.created_at,
        documents=[DocumentOperator.model_validate(d) for d in app.documents],
        missing=missing_types(app),
        history=[AuditEventOut.model_validate(e) for e in history],
    )


@router.get("/documents/{doc_id}/file")
def document_file(doc_id: str, session: Session = Depends(get_session)) -> FileResponse:
    doc = _doc(session, doc_id)
    return FileResponse(storage.path(doc.storage_key), media_type=doc.mime, content_disposition_type="inline")


@router.patch("/documents/{doc_id}/fields", response_model=DocumentOperator)
def update_fields(
    doc_id: str,
    body: FieldsUpdate,
    op: Operator = Depends(require_operator),
    session: Session = Depends(get_session),
) -> DocumentOperator:
    doc = _doc(session, doc_id)
    fields = dict(doc.fields)
    changes = {}
    for name, value in body.fields.items():
        if name not in fields:
            raise HTTPException(422, f"Неизвестное поле: {name}")
        changes[name] = {"old": fields[name].get("value"), "new": value}
        fields[name] = {"value": value, "confidence": 1.0, "issues": [], "edited_by": op.username}
    doc.fields = fields  # reassign so SQLAlchemy sees the JSON change
    audit(session, doc.application_id, f"operator:{op.username}", "fields_edited", doc.id, changes=changes)
    session.commit()
    return DocumentOperator.model_validate(doc)


@router.post("/documents/{doc_id}/reprocess", response_model=DocumentOperator)
def reprocess(
    doc_id: str, op: Operator = Depends(require_operator), session: Session = Depends(get_session)
) -> DocumentOperator:
    doc = _doc(session, doc_id)
    doc.status, doc.status_reason = DocumentStatus.queued, None
    queue.enqueue(session, doc.id)
    audit(session, doc.application_id, f"operator:{op.username}", "reprocess_requested", doc.id)
    refresh_status(doc.application)
    session.commit()
    return DocumentOperator.model_validate(doc)


@router.get("/processing", response_model=list[ProcessingItem])
def processing(session: Session = Depends(get_session)) -> list[ProcessingItem]:
    """In work right now: real documents waiting for or going through parsing (case 3.3)."""
    rows = session.execute(
        select(Document, Application.full_name, Job)
        .join(Application, Application.id == Document.application_id)
        .join(Job, Job.document_id == Document.id)
        .where(Document.status.in_(IN_PROGRESS), Job.status.in_([JobStatus.queued, JobStatus.running]))
        .order_by(Document.created_at)
    ).all()
    return [
        ProcessingItem(
            document_id=d.id,
            application_id=d.application_id,
            full_name=name,
            filename=d.filename,
            status=d.status,
            attempts=j.attempts,
            last_error=j.last_error,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d, name, j in rows
    ]


@router.get("/stats", response_model=QueueStats)
def stats(session: Session = Depends(get_session)) -> QueueStats:
    counts = dict(session.execute(select(Job.status, func.count()).group_by(Job.status)).all())
    avg = session.scalar(select(func.avg(Document.processing_ms)).where(Document.processing_ms.is_not(None)))
    return QueueStats(
        queued=counts.get(JobStatus.queued, 0),
        running=counts.get(JobStatus.running, 0),
        done=counts.get(JobStatus.done, 0),
        failed=counts.get(JobStatus.failed, 0),
        avg_processing_ms=int(avg) if avg is not None else None,
    )
