"""Countries, document types, fields and check rules (case section 4.1) — the single source of truth.

Frontend reads it via GET /api/public/countries. Fields are generic per document type — never values from samples.
`required=True` marks the case's "минимум полей": without them the document counts as not parsed.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime

EXPIRING_SOON_DAYS = 30


@dataclass(frozen=True)
class FieldSpec:
    name: str  # snake_case English key
    label: str  # Russian label for UI
    kind: str = "string"  # string | date | digits
    required: bool = False  # part of the case's minimum set
    pattern: str | None = None  # regex the normalized value must match
    rules: tuple[str, ...] = ()  # not_future | not_expired | latin
    hint: str = ""  # extra instruction for the model


@dataclass(frozen=True)
class DocType:
    code: str
    label: str
    description: str  # how to recognize it (classification prompt)
    fields: list[FieldSpec] = field(default_factory=list)


def _name(required: bool = True, rules: tuple[str, ...] = ()) -> FieldSpec:
    return FieldSpec("full_name", "ФИО", required=required, rules=rules, hint="фамилия, имя, отчество одной строкой")


DOC_TYPES: dict[str, DocType] = {
    dt.code: dt
    for dt in [
        DocType(
            "passport_ru",
            "Паспорт РФ (главный разворот)",
            "Внутренний паспорт гражданина Российской Федерации, разворот с фотографией.",
            [
                FieldSpec("series", "Серия", kind="digits", required=True, pattern=r"^\d{4}$"),
                FieldSpec("number", "Номер", kind="digits", required=True, pattern=r"^\d{6}$"),
                _name(),
                FieldSpec("birth_date", "Дата рождения", kind="date", required=True, rules=("not_future",)),
                FieldSpec("birth_place", "Место рождения"),
                FieldSpec("issued_by", "Кем выдан"),
                FieldSpec("issue_date", "Дата выдачи", kind="date", rules=("not_future",)),
            ],
        ),
        DocType(
            "snils",
            "СНИЛС",
            "Страховое свидетельство / уведомление о регистрации в системе индивидуального учёта (СНИЛС).",
            [
                FieldSpec("number", "Номер", kind="digits", required=True, pattern=r"^\d{11}$"),
                _name(required=False),
            ],
        ),
        DocType(
            "inn",
            "ИНН физического лица",
            "Свидетельство о постановке на учёт физического лица в налоговом органе (ИНН).",
            [FieldSpec("number", "ИНН", kind="digits", required=True, pattern=r"^\d{12}$")],
        ),
        DocType(
            "passport_uz",
            "Паспорт гражданина Узбекистана",
            "Паспорт или ID-карта гражданина Республики Узбекистан (O'zbekiston Respublikasi).",
            [
                FieldSpec("number", "Номер", required=True),
                _name(),
                FieldSpec("birth_date", "Дата рождения", kind="date", rules=("not_future",)),
                FieldSpec("expiry_date", "Срок действия", kind="date", rules=("not_expired",)),
            ],
        ),
        DocType(
            "migration_card",
            "Миграционная карта",
            "Миграционная карта иностранного гражданина при въезде в РФ.",
            [
                FieldSpec("number", "Номер", required=True),
                FieldSpec("entry_date", "Дата въезда", kind="date", rules=("not_future",)),
                FieldSpec("valid_until", "Действует до", kind="date"),
            ],
        ),
        DocType(
            "work_patent",
            "Патент на работу",
            "Патент на осуществление трудовой деятельности иностранным гражданином в РФ (МВД России). "
            "Лицевая сторона: серия, номер, ФИО, гражданство; оборот: территория действия, даты.",
            [
                FieldSpec("series", "Серия", kind="digits"),
                FieldSpec("number", "Номер", required=True, hint="номер патента после знака «№» рядом с серией"),
                FieldSpec("blank_number", "Номер бланка", hint="буквенно-цифровой номер бланка, обычно внизу оборота"),
                _name(required=False),
                FieldSpec("birth_date", "Дата рождения", kind="date", rules=("not_future",)),
                FieldSpec("citizenship", "Гражданство"),
                FieldSpec("issue_date", "Дата выдачи", kind="date", rules=("not_future",)),
                FieldSpec("valid_until", "Действует до", kind="date", required=True, rules=("not_expired",)),
                FieldSpec("region", "Регион (территория действия)"),
            ],
        ),
        DocType(
            "eu_id",
            "Удостоверение личности / загранпаспорт гражданина ЕС",
            "ID-карта или паспорт гражданина страны Евросоюза (European Union).",
            [
                FieldSpec("number", "Номер", required=True),
                _name(rules=("latin",)),
                FieldSpec("birth_date", "Дата рождения", kind="date", rules=("not_future",)),
                FieldSpec("citizenship", "Гражданство"),
                FieldSpec("expiry_date", "Срок действия", kind="date", rules=("not_expired",)),
            ],
        ),
        DocType(
            "residence_permit",
            "Вид на жительство",
            "Вид на жительство / residence permit.",
            [
                FieldSpec("number", "Номер", required=True),
                FieldSpec("issue_date", "Дата выдачи", kind="date", rules=("not_future",)),
                FieldSpec("expiry_date", "Срок действия", kind="date", required=True, rules=("not_expired",)),
                FieldSpec("permit_type", "Тип разрешения"),
            ],
        ),
        # --- types present in the organizers' open test set (case_docs/) — country mapping pending, see questions.md
        DocType(
            "driver_license_ru",
            "Водительское удостоверение РФ",
            "Водительское удостоверение Российской Федерации (RUS, permis de conduire), лицевая сторона или оборот.",
            [
                FieldSpec("number", "Номер", kind="digits", required=True, pattern=r"^\d{10}$", hint="поле 5"),
                _name(),
                FieldSpec("birth_date", "Дата рождения", kind="date", rules=("not_future",)),
                FieldSpec("issue_date", "Дата выдачи", kind="date", rules=("not_future",), hint="поле 4a"),
                FieldSpec("expiry_date", "Действует до", kind="date", rules=("not_expired",), hint="поле 4b"),
                FieldSpec("categories", "Категории", hint="через запятую"),
            ],
        ),
        DocType(
            "driver_license_kg",
            "Водительское удостоверение Киргизии",
            "Водительское удостоверение Кыргызской Республики (KG, айдоочулук күбөлүк).",
            [
                FieldSpec("number", "Номер", required=True, hint="поле 5"),
                _name(),
                FieldSpec("birth_date", "Дата рождения", kind="date", rules=("not_future",)),
                FieldSpec("issue_date", "Дата выдачи", kind="date", rules=("not_future",), hint="поле 4a"),
                FieldSpec("expiry_date", "Действует до", kind="date", rules=("not_expired",), hint="поле 4b"),
                FieldSpec("personal_number", "Персональный номер", hint="поле 4d"),
            ],
        ),
        DocType(
            "passport_by",
            "Паспорт гражданина Беларуси",
            "Паспорт Республики Беларусь (REPUBLIC OF BELARUS, BLR).",
            [
                FieldSpec("number", "Номер", required=True, pattern=r"^[A-Z]{2}\d{7}$"),
                _name(rules=("latin",)),
                FieldSpec("birth_date", "Дата рождения", kind="date", rules=("not_future",)),
                FieldSpec("expiry_date", "Срок действия", kind="date", rules=("not_expired",)),
                FieldSpec("personal_number", "Идентификационный номер"),
            ],
        ),
        DocType(
            "passport_in",
            "Паспорт гражданина Индии",
            "Паспорт Республики Индия (REPUBLIC OF INDIA, IND).",
            [
                FieldSpec("number", "Номер", required=True, pattern=r"^[A-Z]\d{7}$"),
                _name(rules=("latin",)),
                FieldSpec("birth_date", "Дата рождения", kind="date", rules=("not_future",)),
                FieldSpec("expiry_date", "Срок действия", kind="date", rules=("not_expired",)),
            ],
        ),
    ]
}

# Required document set per country — decided on the server, the client only picks the country.
COUNTRIES: dict[str, tuple[str, list[str]]] = {
    "RU": ("Россия", ["passport_ru", "snils", "inn"]),
    "UZ": ("Узбекистан", ["passport_uz", "migration_card", "work_patent"]),
    "EU": ("Страна Евросоюза", ["eu_id", "residence_permit"]),
}

UNKNOWN = "unknown"


def classification_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "doc_type": {"type": "string", "enum": [*DOC_TYPES, UNKNOWN]},
            "readable": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["doc_type", "readable"],
    }


def extraction_schema(dt: DocType) -> dict:
    field_obj = {
        "type": "object",
        "properties": {"value": {"type": ["string", "null"]}, "confidence": {"type": "number"}},
        "required": ["value", "confidence"],
    }
    return {
        "type": "object",
        "properties": {"fields": {"type": "object", "properties": {f.name: field_obj for f in dt.fields}}},
        "required": ["fields"],
    }


def parse_date(value: str) -> date | None:
    formats = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %m %Y", "%d %b %Y", "%d %B %Y")
    for fmt in (*formats, "%d.%m.%y", "%d/%m/%y"):  # two-digit years: 94 → 1994, 27 → 2027
        try:
            return datetime.strptime(value.strip().title(), fmt).date()
        except ValueError:
            continue
    return None


def _check_rules(spec: FieldSpec, value: str, today: date) -> list[str]:
    issues = []
    if spec.kind == "date":
        d = date.fromisoformat(value)
        if "not_future" in spec.rules and d > today:
            issues.append("Дата в будущем")
        if "not_expired" in spec.rules:
            if d < today:
                issues.append("Срок действия истёк")
            elif (d - today).days <= EXPIRING_SOON_DAYS:
                issues.append(f"Истекает через {(d - today).days} дн.")
    if "latin" in spec.rules and re.search(r"[А-Яа-яЁё]", value):
        issues.append("Ожидается латиница")
    return issues


def fields_from(data: dict) -> dict:
    """Models don't always keep the shape: accept {"fields": {...}} or the fields at top level."""
    inner = data.get("fields")
    return inner if isinstance(inner, dict) else data


def validate(dt: DocType, raw_fields: dict, today: date | None = None) -> dict[str, dict]:
    """Normalize model output and apply the case's check rules. Returns {name: {value, confidence, issues}}."""
    today = today or date.today()
    out: dict[str, dict] = {}
    for spec in dt.fields:
        item = raw_fields.get(spec.name) or {}
        if not isinstance(item, dict):  # plain value instead of {value, confidence}
            item = {"value": str(item), "confidence": 0.5}
        value = item.get("value")
        value = value.strip() if isinstance(value, str) and value.strip() else None
        conf = min(max(float(item.get("confidence") or 0.0), 0.0), 1.0)
        issues: list[str] = []
        if value is not None and spec.kind == "digits":
            value = re.sub(r"\D", "", value) or None
        if value is not None and spec.kind == "date":
            d = parse_date(value)
            if d is None:
                issues.append("Не удалось распознать дату")
            else:
                value = d.isoformat()
        if value is None:
            if spec.required:
                issues.append("Обязательное поле не найдено")
        elif not issues:
            if spec.pattern and not re.match(spec.pattern, value):
                issues.append("Неверный формат")
            issues += _check_rules(spec, value, today)
        out[spec.name] = {"value": value, "confidence": round(conf, 2), "issues": issues}
    return out


def missing_required(dt: DocType, fields: dict[str, dict]) -> list[str]:
    """Labels of minimum fields without a value → the document counts as not parsed."""
    return [f.label for f in dt.fields if f.required and not fields.get(f.name, {}).get("value")]


# Letters that look the same in Cyrillic and Latin — OCR mixes them up (ВУ-123 vs BY-123).
_HOMOGLYPHS = str.maketrans("АВЕКМНОРСТУХЁ", "ABEKMHOPCTYXE")


def _norm_text(text: str) -> str:
    return "".join(ch for ch in text.upper().translate(_HOMOGLYPHS) if ch.isalnum())


NOT_IN_TEXT = "Нет в распознанном тексте — сверьте с оригиналом"


def check_grounded(dt: DocType, fields: dict[str, dict], text: str) -> None:
    """Anti-hallucination: when we have the recognized text (OCR or PDF layer), every word of a non-date value must
    occur in it. Otherwise the model made it up → low confidence + issue for the operator. Mutates `fields`."""
    haystack = _norm_text(text)
    if len(haystack) < 20:  # no usable text to compare with
        return
    kinds = {f.name: f.kind for f in dt.fields}
    for name, item in fields.items():
        value = item.get("value")
        if not value or kinds.get(name) == "date":
            continue
        words = [w for w in (_norm_text(part) for part in value.split()) if len(w) >= 2]
        if words and not all(w in haystack for w in words):
            item["issues"] = [*item["issues"], NOT_IN_TEXT]
            item["confidence"] = min(item["confidence"], 0.4)
