"""Uploaded files live on the `files` docker volume (not in the repo). Metadata is in Postgres.
Files are served only through authenticated operator endpoints."""

import uuid
from pathlib import Path

from app.config import settings


def _root() -> Path:
    root = Path(settings.storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def save(data: bytes) -> str:
    key = uuid.uuid4().hex
    (_root() / key).write_bytes(data)
    return key


def path(key: str) -> Path:
    return _root() / key


def read(key: str) -> bytes:
    return path(key).read_bytes()
