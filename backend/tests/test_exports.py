from datetime import date
from types import SimpleNamespace

from app.exports import card_csv, expiring_csv, expiring_rows
from app.models import DocumentStatus


def app_with(valid_until):
    fields = {
        "number": {"value": "123", "confidence": 0.9, "issues": []},
        "valid_until": {"value": valid_until, "confidence": 0.9, "issues": [], "edited_by": "op"},
    }
    d = SimpleNamespace(
        id="d",
        filename="d.jpg",
        detected_type="work_patent",
        declared_type="work_patent",
        status=DocumentStatus.done,
        fields=fields,
    )
    return SimpleNamespace(
        id="a", full_name="Иван Иванов", country="UZ", phone=None, doc_set=["work_patent"], documents=[d]
    )


def test_expiring_selection():
    today = date(2026, 1, 1)
    apps = [app_with("2025-12-01"), app_with("2026-01-20"), app_with("2027-01-01")]
    rows = expiring_rows(apps, 30, today)
    assert [r["days_left"] for r in rows] == [-31, 19]


def test_csv_has_bom_and_cyrillic():
    rows = expiring_rows([app_with("2025-12-01")], 30, date(2026, 1, 1))
    data = expiring_csv(rows)
    assert data.startswith(b"\xef\xbb\xbf")
    assert "Иван Иванов" in data.decode("utf-8-sig")


def test_card_csv_marks_source():
    text = card_csv(app_with("2027-01-01")).decode("utf-8-sig")
    assert "оператор" in text and "модель" in text


def test_csv_neutralizes_formulas():
    from app.exports import to_csv

    out = to_csv(["a"], [['=HYPERLINK("x")'], ["-1"], ["Иванов"]]).decode("utf-8-sig")
    assert "'=HYPERLINK" in out and "'-1" in out and "\nИванов" in out
