"""HTTP contract (source of truth). After changes: `make openapi`, frontend: `npm run gen:api`."""

from datetime import date as Date
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ApplicationStatus, DocumentStatus


class FieldSpecOut(BaseModel):
    name: str
    label: str
    required: bool


class DocTypeOut(BaseModel):
    code: str
    label: str
    fields: list[FieldSpecOut]


class CountryOut(BaseModel):
    code: str
    label: str
    doc_types: list[DocTypeOut]  # required set for this country


class ApplicationCreate(BaseModel):
    full_name: str
    country: str  # CountryOut.code; the server derives the document set from it
    phone: str | None = None


class ApplicationCreated(BaseModel):
    id: str
    token: str  # shown once; applicant sends it as X-Application-Token


class ExtractedField(BaseModel):
    value: str | None
    confidence: float
    issues: list[str] = []
    edited_by: str | None = None  # operator username if corrected by hand


class SlotPublic(BaseModel):
    """One document type in the application (may consist of several files)."""

    doc_type: str
    label: str
    required: bool
    state: str  # missing | processing | ok | problem
    document_ids: list[str]
    missing_fields: list[str]  # labels of minimum fields not found across all files
    warnings: list[str] = []  # e.g. the same document uploaded twice as different files


class MergedField(ExtractedField):
    document_id: str | None  # file the value came from (edit goes there)
    label: str = ""  # Russian field label (works for every document type, not only country sets)


class SlotOperator(SlotPublic):
    fields: dict[str, MergedField]


class DocumentPublic(BaseModel):
    """What the applicant sees: status only, no extracted personal data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    declared_type: str | None
    filename: str
    status: DocumentStatus
    status_reason: str | None
    created_at: datetime


class ApplicationPublic(BaseModel):
    id: str
    status: ApplicationStatus
    full_name: str
    country: str
    doc_set: list[str]
    slots: list[SlotPublic]
    documents: list[DocumentPublic]
    missing: list[str]  # doc type codes from doc_set without a usable document


class DocumentOperator(DocumentPublic):
    detected_type: str | None
    ocr_text: str | None
    mime: str
    size: int
    fields: dict[str, ExtractedField]
    llm_meta: dict
    processing_ms: int | None
    updated_at: datetime


class ApplicationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ApplicationStatus
    full_name: str
    country: str
    created_at: datetime
    updated_at: datetime
    documents_total: int
    documents_done: int
    documents_attention: int  # needs_review / unreadable / failed


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor: str
    action: str
    document_id: str | None
    data: dict
    created_at: datetime


class ApplicationOperator(BaseModel):
    id: str
    status: ApplicationStatus
    full_name: str
    phone: str | None
    country: str
    doc_set: list[str]
    created_at: datetime
    slots: list[SlotOperator]
    cross_checks: list[str] = []  # name / birth date mismatches between documents and the typed name
    documents: list[DocumentOperator]
    missing: list[str]
    history: list[AuditEventOut]


class FieldsUpdate(BaseModel):
    fields: dict[str, str | None]  # operator corrections: field name → new value


class ProcessingItem(BaseModel):
    document_id: str
    application_id: str
    full_name: str
    filename: str
    status: DocumentStatus
    attempts: int
    last_error: str | None  # human-readable (Russian) reason; raw technical error stays in worker logs
    created_at: datetime
    updated_at: datetime


class QueueStats(BaseModel):
    queued: int
    running: int
    done: int
    failed: int
    avg_processing_ms: int | None


class Me(BaseModel):
    username: str
    roles: list[str]


class ExpiringItem(BaseModel):
    application_id: str
    full_name: str
    doc_type: str
    doc_label: str
    field: str
    date: Date
    days_left: int  # negative = already expired
