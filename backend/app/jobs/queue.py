"""Durable job queue on Postgres. The job row is the source of truth — a restart loses nothing:
an unfinished job either stays `queued` or is `running` with an expiring lease that another worker re-claims."""

from datetime import timedelta

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Job, JobStatus, utcnow


def enqueue(session: Session, document_id: str) -> Job:
    job = Job(document_id=document_id)
    session.add(job)
    return job


def claim(session: Session, worker_id: str) -> Job | None:
    now = utcnow()
    stmt = (
        select(Job)
        .where(
            or_(
                and_(Job.status == JobStatus.queued, Job.run_after <= now),
                and_(Job.status == JobStatus.running, Job.locked_until < now),  # lease expired: worker died
            )
        )
        .order_by(Job.run_after)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = session.scalars(stmt).first()
    if job is None:
        return None
    job.status = JobStatus.running
    job.locked_by = worker_id
    job.locked_until = now + timedelta(seconds=settings.job_lease_s)
    job.attempts += 1
    session.commit()
    return job


def extend_lease(job_id: int) -> None:
    """Called periodically by a keep-alive thread while the job runs (own session: the main one may be busy)."""
    with SessionLocal() as session:
        session.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == JobStatus.running)
            .values(locked_until=utcnow() + timedelta(seconds=settings.job_lease_s))
        )
        session.commit()


def release_own(worker_prefix: str) -> int:
    """On worker start: jobs this worker held before a restart go straight back to the queue (no lease wait)."""
    with SessionLocal() as session:
        result = session.execute(
            update(Job)
            .where(Job.status == JobStatus.running, Job.locked_by.like(f"{worker_prefix}-%"))
            .values(status=JobStatus.queued, locked_until=None, run_after=utcnow())
        )
        session.commit()
        return result.rowcount


def finish(session: Session, job: Job) -> None:
    job.status, job.locked_until, job.last_error = JobStatus.done, None, None
    session.commit()


def retry_or_fail(session: Session, job: Job, error: str, retryable: bool) -> bool:
    """Returns True if the job will be retried."""
    job.last_error = error[:2000]
    job.locked_until = None
    if retryable and job.attempts < settings.job_max_attempts:
        job.status = JobStatus.queued
        job.run_after = utcnow() + timedelta(seconds=10 * 2 ** (job.attempts - 1))
        session.commit()
        return True
    job.status = JobStatus.failed
    session.commit()
    return False
