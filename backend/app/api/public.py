"""Applicant API. No login: creating an application returns a secret token; all calls require X-Application-Token.
Every upload check happens here, on the server (Д2). Upload returns 202 immediately; parsing is in the worker (Д7)."""

import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import storage
from app.applications import audit, missing_types, refresh_status
from app.config import settings
from app.db import get_session
from app.extraction.doctypes import DOC_TYPES
from app.extraction.preprocess import ALLOWED_MIME, sniff_mime
from app.jobs import queue
from app.models import Application, ApplicationStatus, Document, new_id
from app.schemas import (
    ApplicationCreate,
    ApplicationCreated,
    ApplicationPublic,
    DocTypeOut,
    DocumentPublic,
    FieldSpecOut,
)

router = APIRouter(prefix="/api/public", tags=["applicant"])


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _load(session: Session, app_id: str, token: str | None) -> Application:
    app = session.get(Application, app_id)
    # same 404 for "no such id" and "wrong token" — don't reveal which applications exist
    if app is None or not token or not hmac.compare_digest(app.applicant_token_hash, _hash(token)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
    return app


def _public(app: Application) -> ApplicationPublic:
    return ApplicationPublic(
        id=app.id,
        status=app.status,
        doc_set=app.doc_set,
        documents=[DocumentPublic.model_validate(d) for d in app.documents],
        missing=missing_types(app),
    )


@router.get("/doc-types", response_model=list[DocTypeOut])
def doc_types() -> list[DocTypeOut]:
    return [
        DocTypeOut(
            code=dt.code,
            label=dt.label,
            fields=[FieldSpecOut(name=f.name, label=f.label, required=f.required) for f in dt.fields],
        )
        for dt in DOC_TYPES.values()
    ]


@router.post("/applications", status_code=status.HTTP_201_CREATED, response_model=ApplicationCreated)
def create_application(body: ApplicationCreate, session: Session = Depends(get_session)) -> ApplicationCreated:
    unknown = [c for c in body.doc_set if c not in DOC_TYPES]
    if not body.doc_set or unknown or len(set(body.doc_set)) != len(body.doc_set):
        raise HTTPException(422, "Выберите набор документов из списка, без повторов")
    token = secrets.token_urlsafe(32)
    app = Application(doc_set=body.doc_set, applicant_token_hash=_hash(token))
    session.add(app)
    session.flush()
    audit(session, app.id, "applicant", "application_created", doc_set=body.doc_set)
    session.commit()
    return ApplicationCreated(id=app.id, token=token)


@router.get("/applications/{app_id}", response_model=ApplicationPublic)
def get_application(
    app_id: str,
    x_application_token: str | None = Header(None),
    session: Session = Depends(get_session),
) -> ApplicationPublic:
    return _public(_load(session, app_id, x_application_token))


@router.post("/applications/{app_id}/documents", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentPublic)
def upload_document(
    app_id: str,
    file: UploadFile = File(...),
    declared_type: str | None = Form(None),
    x_application_token: str | None = Header(None),
    session: Session = Depends(get_session),
) -> DocumentPublic:
    app = _load(session, app_id, x_application_token)
    if app.status in (ApplicationStatus.accepted, ApplicationStatus.rejected):
        raise HTTPException(409, "Заявка уже рассмотрена, загрузка закрыта")
    if declared_type is not None and declared_type not in app.doc_set:
        raise HTTPException(422, "Этот вид документа не входит в выбранный набор")

    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    if not data:
        raise HTTPException(400, "Файл пустой")
    if len(data) > limit:
        raise HTTPException(413, f"Файл больше {settings.max_upload_mb} МБ")
    mime = sniff_mime(data)
    if mime not in ALLOWED_MIME:
        raise HTTPException(415, "Поддерживаются только PDF, JPG и PNG (проверяется содержимое, а не расширение)")

    sha = hashlib.sha256(data).hexdigest()
    if any(d.sha256 == sha for d in app.documents):
        raise HTTPException(409, "Этот файл уже загружен в заявку") from None

    doc = Document(
        id=new_id(),
        application_id=app.id,
        declared_type=declared_type,
        filename=(file.filename or "file")[:255],
        mime=mime,
        size=len(data),
        sha256=sha,
        storage_key=storage.save(data),
    )
    session.add(doc)
    queue.enqueue(session, doc.id)
    audit(session, app.id, "applicant", "document_uploaded", doc.id, filename=doc.filename, declared_type=declared_type)
    try:
        session.flush()
    except IntegrityError:  # concurrent duplicate upload
        session.rollback()
        raise HTTPException(409, "Этот файл уже загружен в заявку") from None
    session.refresh(app)
    refresh_status(app)
    session.commit()
    return DocumentPublic.model_validate(doc)
