from types import SimpleNamespace

from app.applications import doc_slots
from app.models import DocumentStatus


def doc(id, fields, status=DocumentStatus.done):
    full = {k: {"value": v, "confidence": c, "issues": []} for k, (v, c) in fields.items()}
    patent = "work_patent"
    return SimpleNamespace(
        id=id, filename=f"{id}.jpg", detected_type=patent, declared_type=patent, status=status, fields=full
    )


def test_front_and_back_merge_into_one_document():
    front = doc("f", {"number": ("2619509710", 0.95), "full_name": ("ХАКИМОВ ТИМУР", 0.95)})
    back = doc("b", {"valid_until": ("2027-08-29", 0.98)})
    app = SimpleNamespace(doc_set=["work_patent"], documents=[front, back])
    [slot] = doc_slots(app)
    assert slot["missing_fields"] == []
    assert slot["fields"]["number"]["document_id"] == "f"
    assert slot["fields"]["valid_until"]["document_id"] == "b"
    assert slot["fields"]["valid_until"]["label"] == "Действует до"
    assert slot["state"] == "ok"


def test_conflicting_values_are_flagged():
    a = doc("a", {"number": ("111", 0.9), "valid_until": ("2027-01-01", 0.9)})
    b = doc("b", {"number": ("222", 0.8)})
    [slot] = doc_slots(SimpleNamespace(doc_set=["work_patent"], documents=[a, b]))
    assert slot["fields"]["number"]["value"] == "111"
    assert "разные значения" in slot["fields"]["number"]["issues"][0]
    assert slot["state"] == "problem"


def test_missing_document_type():
    [slot] = doc_slots(SimpleNamespace(doc_set=["inn"], documents=[]))
    assert slot["state"] == "missing"


def test_same_document_uploaded_twice_is_flagged():
    a = doc("a", {"series": ("77", 0.9), "number": ("2698835778", 0.9), "valid_until": ("2027-01-01", 0.9)})
    b = doc("b", {"series": ("77", 0.9), "number": ("2698835778", 0.9)})
    a.filename, b.filename = "patent.jpg", "patent (копия).jpg"
    [slot] = doc_slots(SimpleNamespace(doc_set=["work_patent"], documents=[a, b]))
    assert slot["warnings"] and "один и тот же документ" in slot["warnings"][0]
    assert slot["state"] == "problem"
