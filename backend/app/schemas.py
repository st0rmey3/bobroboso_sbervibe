"""HTTP contract (source of truth). After changes: `make openapi`, frontend: `npm run gen:api`."""

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


class ApplicationCreate(BaseModel):
    doc_set: list[str]  # doc type codes the applicant will provide


class ApplicationCreated(BaseModel):
    id: str
    token: str  # shown once; applicant sends it as X-Application-Token


class ExtractedField(BaseModel):
    value: str | None
    confidence: float
    issues: list[str] = []


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
    doc_set: list[str]
    documents: list[DocumentPublic]
    missing: list[str]  # doc type codes from doc_set without a usable document


class DocumentOperator(DocumentPublic):
    detected_type: str | None
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
    created_at: datetime
    updated_at: datetime
    documents_total: int
    documents_done: int


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
    doc_set: list[str]
    created_at: datetime
    documents: list[DocumentOperator]
    missing: list[str]
    history: list[AuditEventOut]


class FieldsUpdate(BaseModel):
    fields: dict[str, str | None]  # operator corrections: field name → new value


class QueueStats(BaseModel):
    queued: int
    running: int
    done: int
    failed: int
    avg_processing_ms: int | None


class Me(BaseModel):
    username: str
    roles: list[str]
