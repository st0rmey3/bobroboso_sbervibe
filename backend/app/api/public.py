"""Applicant API. No login: creating an application returns a secret token; all calls require X-Application-Token.
Every upload check happens here, on the server (Д2), and every refusal is written to the audit log (case 5.1).
Upload returns 202 immediately; parsing happens in the worker (Д7)."""

import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import storage
from app.applications import audit, doc_slots, missing_types, refresh_status
from app.config import settings
from app.db import get_session
from app.extraction.doctypes import COUNTRIES, DOC_TYPES
from app.extraction.preprocess import ALLOWED_MIME, sniff_mime
from app.jobs import queue
from app.models import Application, ApplicationStatus, Document, new_id
from app.schemas import (
    ApplicationCreate,
    ApplicationCreated,
    ApplicationPublic,
    CountryOut,
    DocTypeOut,
    DocumentPublic,
    FieldSpecOut,
    SlotPublic,
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


def _reject(session: Session, app: Application, code: int, reason: str, **data) -> HTTPException:
    """Log the refusal (who/when/why) and return the error to raise."""
    audit(session, app.id, "applicant", "upload_rejected", reason=reason, **data)
    session.commit()
    return HTTPException(code, reason)


def _public(app: Application) -> ApplicationPublic:
    return ApplicationPublic(
        id=app.id,
        status=app.status,
        full_name=app.full_name,
        country=app.country,
        doc_set=app.doc_set,
        slots=[SlotPublic.model_validate(s) for s in doc_slots(app)],
        documents=[DocumentPublic.model_validate(d) for d in app.documents],
        missing=missing_types(app),
    )


@router.get("/countries", response_model=list[CountryOut])
def countries() -> list[CountryOut]:
    return [
        CountryOut(
            code=code,
            label=label,
            doc_types=[
                DocTypeOut(
                    code=dt.code,
                    label=dt.label,
                    fields=[FieldSpecOut(name=f.name, label=f.label, required=f.required) for f in dt.fields],
                )
                for dt in (DOC_TYPES[c] for c in doc_set)
            ],
        )
        for code, (label, doc_set) in COUNTRIES.items()
    ]


@router.post("/applications", status_code=status.HTTP_201_CREATED, response_model=ApplicationCreated)
def create_application(body: ApplicationCreate, session: Session = Depends(get_session)) -> ApplicationCreated:
    full_name = " ".join(body.full_name.split())
    if len(full_name) < 3:
        raise HTTPException(422, "Укажите фамилию и имя")
    if body.country not in COUNTRIES:
        raise HTTPException(422, "Выберите страну из списка")
    token = secrets.token_urlsafe(32)
    app = Application(
        full_name=full_name,
        phone=(body.phone or "").strip() or None,
        country=body.country,
        doc_set=COUNTRIES[body.country][1],
        applicant_token_hash=_hash(token),
    )
    session.add(app)
    session.flush()
    audit(session, app.id, "applicant", "application_created", country=body.country)
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
    declared_type: str | None = Form(None),  # None = "не знаю, какой это документ": type comes from the content
    x_application_token: str | None = Header(None),
    session: Session = Depends(get_session),
) -> DocumentPublic:
    app = _load(session, app_id, x_application_token)
    name = (file.filename or "file")[:255]
    if app.status in (ApplicationStatus.accepted, ApplicationStatus.rejected):
        raise _reject(session, app, 409, "Заявка уже рассмотрена, загрузка закрыта", filename=name)
    if declared_type is not None and declared_type not in DOC_TYPES:
        raise _reject(session, app, 422, "Неизвестный вид документа", filename=name)
    if len(app.documents) >= settings.max_files_per_application:
        raise _reject(session, app, 413, f"В заявке уже {settings.max_files_per_application} файлов — это максимум")

    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    if not data:
        raise _reject(session, app, 400, "Файл пустой", filename=name)
    if len(data) > limit:
        raise _reject(session, app, 413, f"Файл больше {settings.max_upload_mb} МБ", filename=name)
    if sum(d.size for d in app.documents) + len(data) > settings.max_application_mb * 1024 * 1024:
        raise _reject(session, app, 413, f"Общий объём заявки больше {settings.max_application_mb} МБ", filename=name)
    mime = sniff_mime(data)
    if mime not in ALLOWED_MIME:
        raise _reject(session, app, 415, "Поддерживаются только PDF, JPG, PNG и WEBP", filename=name)

    sha = hashlib.sha256(data).hexdigest()
    if any(d.sha256 == sha for d in app.documents):
        raise _reject(session, app, 409, "Этот файл уже загружен в заявку", filename=name)

    doc = Document(
        id=new_id(),
        application_id=app.id,
        declared_type=declared_type,
        filename=name,
        mime=mime,
        size=len(data),
        sha256=sha,
        storage_key=storage.save(data),
    )
    session.add(doc)
    queue.enqueue(session, doc.id)
    audit(session, app.id, "applicant", "document_uploaded", doc.id, filename=name, declared_type=declared_type)
    try:
        session.flush()
    except IntegrityError:  # concurrent duplicate upload
        session.rollback()
        raise HTTPException(409, "Этот файл уже загружен в заявку") from None
    session.refresh(app)
    refresh_status(app)
    session.commit()
    return DocumentPublic.model_validate(doc)
