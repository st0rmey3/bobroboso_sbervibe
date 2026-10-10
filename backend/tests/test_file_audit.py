"""Opening an original file (personal data) leaves an audit trail, deduplicated per operator."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth import Operator, require_operator
from app.db import SessionLocal, engine, init_db
from app.main import app
from app.models import Application, AuditEvent, Document


def test_file_view_is_audited_once(tmp_path, monkeypatch):
    try:  # needs a database: runs in `make test` (Postgres in docker) or with DATABASE_URL=sqlite:///...
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        pytest.skip("no database")
    monkeypatch.setattr("app.storage.settings.storage_dir", str(tmp_path))
    init_db()
    (tmp_path / "k").write_bytes(b"%PDF-1.4 test")
    with SessionLocal() as s:
        a = Application(full_name="Тест Тестов", country="RU", doc_set=[], applicant_token_hash="x")
        s.add(a)
        s.flush()
        d = Document(application_id=a.id, filename="p.pdf", mime="application/pdf", size=13, sha256="h")
        d.storage_key = "k"
        s.add(d)
        s.commit()
        app_id, doc_id = a.id, d.id
    app.dependency_overrides[require_operator] = lambda: Operator(sub="u", username="op1", roles=["operator"])
    try:
        c = TestClient(app)
        assert c.get(f"/api/operator/documents/{doc_id}/file").status_code == 200
        assert c.get(f"/api/operator/documents/{doc_id}/file").status_code == 200
    finally:
        app.dependency_overrides.clear()
    with SessionLocal() as s:
        views = s.query(AuditEvent).filter_by(application_id=app_id, action="file_viewed").all()
    assert len(views) == 1 and views[0].actor == "operator:op1"
