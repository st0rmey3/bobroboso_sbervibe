import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import logs
from app.api import operator, public
from app.config import settings
from app.db import get_session, init_db
from app.models import Job, JobStatus

logs.setup()
log = logging.getLogger("http")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Приём и разбор документов соискателей", version="0.1.0", lifespan=lifespan)
app.include_router(public.router)
app.include_router(operator.router)


@app.middleware("http")
async def request_log(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    logs.context_id.set(rid)
    t0 = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    log.info(
        "%s %s → %d in %d ms", request.method, request.url.path, response.status_code, (time.monotonic() - t0) * 1000
    )
    return response


@app.get("/api/health", tags=["service"])
def health(session: Session = Depends(get_session)) -> dict:
    session.execute(text("select 1"))
    counts = dict(session.execute(select(Job.status, func.count()).group_by(Job.status)).all())
    queue = {s.value: counts.get(s, 0) for s in JobStatus}
    return {"status": "ok", "llm_provider": settings.llm_provider, "queue": queue}
