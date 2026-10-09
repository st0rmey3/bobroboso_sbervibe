from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session


def init_db() -> None:
    # Hackathon decision (docs/decisions.md): create_all instead of migrations; schema change → `make reset`.
    from app import models  # noqa: F401  (register tables)

    Base.metadata.create_all(engine)
