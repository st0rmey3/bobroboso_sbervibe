import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import operator, public
from app.config import settings
from app.db import get_session, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Приём и разбор документов соискателей", version="0.1.0", lifespan=lifespan)
app.include_router(public.router)
app.include_router(operator.router)


@app.get("/api/health", tags=["service"])
def health(session: Session = Depends(get_session)) -> dict:
    session.execute(text("select 1"))
    return {"status": "ok", "llm_provider": settings.llm_provider}
