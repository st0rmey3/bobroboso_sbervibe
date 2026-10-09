"""Registry of document types and their fields — the single source of truth (frontend reads it via API).

TODO(T-003): replace the example with the 8 document types from docs/case/spec.md.
Rules: fields must be generic for the document type — never values/positions from specific sample files.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class FieldSpec:
    name: str  # snake_case English key
    label: str  # Russian label for UI
    kind: str = "string"  # string | date
    required: bool = True
    pattern: str | None = None  # regex for normalized value
    hint: str = ""  # extra instruction for the model


@dataclass(frozen=True)
class DocType:
    code: str
    label: str
    description: str  # how to recognize it (used in the classification prompt)
    fields: list[FieldSpec] = field(default_factory=list)
    expiry_field: str | None = None  # field with expiry date (bonus: expiring documents)


DOC_TYPES: dict[str, DocType] = {
    dt.code: dt
    for dt in [
        # EXAMPLE — replace / extend with the real list from the case.
        DocType(
            code="passport_ru",
            label="Паспорт гражданина РФ",
            description="Внутренний паспорт РФ: разворот с фото, серия и номер, кем выдан, код подразделения.",
            fields=[
                FieldSpec("last_name", "Фамилия"),
                FieldSpec("first_name", "Имя"),
                FieldSpec("middle_name", "Отчество", required=False),
                FieldSpec("birth_date", "Дата рождения", kind="date"),
                FieldSpec("series_number", "Серия и номер", pattern=r"^\d{4} \d{6}$", hint="формат '1234 567890'"),
                FieldSpec("issue_date", "Дата выдачи", kind="date"),
                FieldSpec("issued_by", "Кем выдан"),
                FieldSpec("department_code", "Код подразделения", pattern=r"^\d{3}-\d{3}$"),
            ],
        ),
    ]
}

UNKNOWN = "unknown"


def classification_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "doc_type": {"type": "string", "enum": [*DOC_TYPES, UNKNOWN]},
            "readable": {"type": "boolean"},
            "confidence": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["doc_type", "readable", "confidence"],
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


def _parse_date(value: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def validate(dt: DocType, raw_fields: dict) -> dict[str, dict]:
    """Normalize model output and add issues. Returns {name: {value, confidence, issues}}."""
    out: dict[str, dict] = {}
    for spec in dt.fields:
        item = raw_fields.get(spec.name) or {}
        value = item.get("value")
        value = value.strip() if isinstance(value, str) and value.strip() else None
        conf = float(item.get("confidence") or 0.0)
        conf = min(max(conf, 0.0), 1.0)
        issues: list[str] = []
        if value is None:
            if spec.required:
                issues.append("Поле не найдено в документе")
        elif spec.kind == "date":
            d = _parse_date(value)
            if d is None:
                issues.append("Не удалось распознать дату")
            else:
                value = d.isoformat()
        if value is not None and spec.pattern and spec.kind != "date" and not re.match(spec.pattern, value):
            issues.append("Формат не совпадает с ожидаемым")
        if issues:
            conf = min(conf, 0.3)
        out[spec.name] = {"value": value, "confidence": round(conf, 2), "issues": issues}
    return out
