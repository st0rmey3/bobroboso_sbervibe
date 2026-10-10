from datetime import date

from app.extraction import doctypes
from app.extraction.preprocess import sniff_mime
from app.llm.base import LLMError, parse_json
from app.llm.ocr import strip_front_matter

TODAY = date(2026, 10, 10)
DT = doctypes.DOC_TYPES


def f(value, confidence=0.9):
    return {"value": value, "confidence": confidence}


def test_country_sets_use_known_types():
    assert len(DT) >= 8
    assert all(c in DT for _, codes in doctypes.COUNTRIES.values() for c in codes)


def test_model_output_shape_is_tolerated():
    assert doctypes.fields_from({"number": "1"}) == {"number": "1"}
    out = doctypes.validate(DT["inn"], {"number": "0278 6192 7020"}, TODAY)
    assert out["number"]["value"] == "027861927020"


def test_passport_ru_normalizes_and_checks():
    out = doctypes.validate(
        DT["passport_ru"],
        {"series": f("45 12"), "number": f("12345"), "birth_date": f("01.02.2030"), "full_name": f("Иванов Иван")},
        TODAY,
    )
    assert out["series"] == {"value": "4512", "confidence": 0.9, "issues": []}
    assert out["number"]["issues"] == ["Неверный формат"]
    assert out["birth_date"]["value"] == "2030-02-01"
    assert out["birth_date"]["issues"] == ["Дата в будущем"]


def test_expired_patent_is_flagged_not_dropped():
    out = doctypes.validate(DT["work_patent"], {"number": f("77 123"), "valid_until": f("01.01.2026")}, TODAY)
    assert out["valid_until"]["issues"] == ["Срок действия истёк"]
    assert doctypes.missing_required(DT["work_patent"], out) == []


def test_missing_minimum_fields():
    out = doctypes.validate(DT["snils"], {}, TODAY)
    assert doctypes.missing_required(DT["snils"], out) == ["Номер"]


def test_eu_name_must_be_latin():
    out = doctypes.validate(DT["eu_id"], {"number": f("X1"), "full_name": f("Мюллер Ханс")}, TODAY)
    assert out["full_name"]["issues"] == ["Ожидается латиница"]


def test_parse_json_strips_fences():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_rejects_garbage():
    try:
        parse_json("no json here")
    except LLMError as e:
        assert e.retryable
    else:
        raise AssertionError


def test_olmocr_front_matter_is_removed():
    assert strip_front_matter("---\nprimary_language: ru\n---\nПАСПОРТ") == "ПАСПОРТ"


def test_sniff_mime_ignores_extension():
    assert sniff_mime(b"%PDF-1.7 ...") == "application/pdf"
    assert sniff_mime(b"MZ\x90\x00") is None


def test_no_empty_bearer_header():
    from app.llm.base import bearer

    assert bearer("") == {}
    assert bearer("k") == {"Authorization": "Bearer k"}


def test_phone_photo_orientation_and_webp():
    import io

    from PIL import Image

    from app.extraction import preprocess

    img = Image.new("RGB", (400, 300), "white")
    exif = img.getexif()
    exif[0x0112] = 6  # "rotate 90° CW to display" — typical portrait phone photo
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif)
    page = Image.open(io.BytesIO(preprocess.load(buf.getvalue(), "image/jpeg").images[0]))
    assert page.size == (300, 400)

    webp = io.BytesIO()
    img.save(webp, "WEBP")
    assert preprocess.sniff_mime(webp.getvalue()) == "image/webp"
    assert preprocess.load(webp.getvalue(), "image/webp").images
