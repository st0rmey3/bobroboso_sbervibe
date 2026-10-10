"""Worker process: `python -m app.jobs.worker`. Runs WORKER_CONCURRENCY threads, each claims jobs from Postgres."""

import logging
import signal
import socket
import threading
import time

from app import logs
from app.applications import audit, refresh_status
from app.config import settings
from app.db import SessionLocal, init_db
from app.extraction.pipeline import process_document
from app.jobs import queue
from app.llm import LLMError
from app.models import Document, DocumentStatus, Job

log = logging.getLogger("worker")
stop = threading.Event()
KEEPALIVE_S = 15


def _keepalive(job_id: int, done: threading.Event) -> None:
    """Extend the job lease while it runs, so a long model call never looks like a dead worker."""
    while not done.wait(KEEPALIVE_S):
        try:
            queue.extend_lease(job_id)
        except Exception:
            log.exception("job %s: lease extension failed", job_id)


def handle(job_id: int) -> None:
    logs.context_id.set(f"job{job_id}")
    done = threading.Event()
    threading.Thread(target=_keepalive, args=(job_id, done), daemon=True).start()
    try:
        _process(job_id)
    finally:
        done.set()


def _process(job_id: int) -> None:
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        doc = session.get(Document, job.document_id)
        try:
            process_document(session, doc)
            queue.finish(session, job)
            audit(session, doc.application_id, "system", "document_processed", doc.id, status=doc.status.value)
        except LLMError as e:
            session.rollback()
            will_retry = queue.retry_or_fail(session, job, str(e), e.retryable)
            doc.status = DocumentStatus.queued if will_retry else DocumentStatus.failed
            doc.status_reason = (
                "Сервис распознавания временно недоступен, повторим автоматически"
                if will_retry
                else "Сервис распознавания недоступен. Оператор может перезапустить разбор."
            )
            log.warning("job %s llm error (retry=%s): %s", job_id, will_retry, e)
        except Exception as e:  # bug in our code: retry a few times, then fail honestly
            session.rollback()
            log.exception("job %s crashed", job_id)
            will_retry = queue.retry_or_fail(session, job, repr(e), retryable=True)
            doc.status = DocumentStatus.queued if will_retry else DocumentStatus.failed
            doc.status_reason = "Повторная попытка разбора" if will_retry else "Внутренняя ошибка разбора"
        refresh_status(doc.application)
        session.commit()


def loop(n: int) -> None:
    worker_id = f"{socket.gethostname()}-{n}"
    while not stop.is_set():
        with SessionLocal() as session:
            job = queue.claim(session, worker_id)
            job_id = job.id if job else None
        if job_id is None:
            stop.wait(1.0)
            continue
        log.info("%s took job %s", worker_id, job_id)
        handle(job_id)


def main() -> None:
    logs.setup()
    init_db()
    released = queue.release_own(socket.gethostname())
    if released:
        log.info("re-queued %d job(s) left running before restart", released)
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    threads = [threading.Thread(target=loop, args=(i,), daemon=True) for i in range(settings.worker_concurrency)]
    for t in threads:
        t.start()
    log.info("worker started: %d threads, provider=%s", len(threads), settings.llm_provider)
    while not stop.is_set():
        time.sleep(0.5)
    for t in threads:
        t.join(timeout=10)


if __name__ == "__main__":
    main()
