from app.extraction import doctypes
from app.extraction.preprocess import sniff_mime
from app.llm.base import LLMError, parse_json

DT = next(iter(doctypes.DOC_TYPES.values()))


def test_validate_normalizes_dates_and_flags_missing():
    date_field = next(f for f in DT.fields if f.kind == "date")
    required = next(f for f in DT.fields if f.required and f.name != date_field.name)
    out = doctypes.validate(DT, {date_field.name: {"value": "01.02.2000", "confidence": 0.9}})
    assert out[date_field.name]["value"] == "2000-02-01"
    assert out[required.name]["value"] is None
    assert out[required.name]["issues"]


def test_parse_json_strips_fences():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_rejects_garbage():
    try:
        parse_json("no json here")
    except LLMError as e:
        assert e.retryable
    else:
        raise AssertionError


def test_sniff_mime_ignores_extension():
    assert sniff_mime(b"%PDF-1.7 ...") == "application/pdf"
    assert sniff_mime(b"MZ\x90\x00") is None
