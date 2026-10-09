"""Durable job queue on Postgres. The job row is the source of truth — a restart loses nothing:
an unfinished job either stays `queued` or is `running` with an expiring lease that another worker re-claims."""

from datetime import timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.config import settings
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


def heartbeat(session: Session, job: Job) -> None:
    job.locked_until = utcnow() + timedelta(seconds=settings.job_lease_s)
    session.commit()


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
