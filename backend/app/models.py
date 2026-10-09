import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid.uuid4())


class ApplicationStatus(enum.StrEnum):
    draft = "draft"  # applicant is still uploading
    processing = "processing"  # some documents are being parsed
    ready = "ready"  # all documents parsed, waiting for operator
    needs_review = "needs_review"  # something needs operator attention
    accepted = "accepted"
    rejected = "rejected"


class DocumentStatus(enum.StrEnum):
    queued = "queued"
    preprocessing = "preprocessing"
    extracting = "extracting"  # model call in progress
    validating = "validating"
    done = "done"
    needs_review = "needs_review"  # parsed, but low confidence / failed checks / type mismatch
    unreadable = "unreadable"  # file content can't be parsed (honest refusal)
    failed = "failed"  # model unavailable after all retries


class JobStatus(enum.StrEnum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.draft)
    # doc type codes the applicant must provide (see extraction/doctypes.py)
    doc_set: Mapped[list[str]] = mapped_column(JSON, default=list)
    applicant_token_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    documents: Mapped[list["Document"]] = relationship(back_populates="application", order_by="Document.created_at")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("application_id", "sha256", name="uq_document_dup"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    declared_type: Mapped[str | None] = mapped_column(String(64))  # slot the applicant uploaded into
    detected_type: Mapped[str | None] = mapped_column(String(64))  # what the model says it is
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(255))
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.queued, index=True)
    # Russian, user-facing reason for unreadable/failed/needs_review
    status_reason: Mapped[str | None] = mapped_column(Text)
    # {field_name: {"value": str|None, "confidence": float, "issues": [str]}}
    fields: Mapped[dict] = mapped_column(JSON, default=dict)
    llm_meta: Mapped[dict] = mapped_column(JSON, default=dict)  # provider, model, latency_ms
    processing_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    application: Mapped[Application] = relationship(back_populates="documents")


class Job(Base):
    """Durable work item. Claimed with SELECT ... FOR UPDATE SKIP LOCKED and a lease (locked_until).
    If a worker dies, the lease expires and another worker re-claims the job — nothing is lost on restart."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    locked_by: Mapped[str | None] = mapped_column(String(64))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AuditEvent(Base):
    """Who changed what and when (bonus: application history)."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(36))
    actor: Mapped[str] = mapped_column(String(128))  # "applicant" | "system" | "operator:<username>"
    action: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
