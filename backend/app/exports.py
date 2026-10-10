"""Operator exports: expiring documents and an applicant card as Excel-friendly CSV (UTF-8 BOM, `;`)."""

import csv
import io
from datetime import date

from app.applications import doc_slots
from app.extraction.doctypes import DOC_TYPES, parse_date


def expiring_rows(applications, days: int, today: date | None = None) -> list[dict]:
    """Expiry fields (rule not_expired) that are already past or end within `days`, most urgent first."""
    today = today or date.today()
    rows = []
    for app in applications:
        for slot in doc_slots(app):
            for spec in DOC_TYPES[slot["doc_type"]].fields:
                if "not_expired" not in spec.rules:
                    continue
                value = slot["fields"][spec.name].get("value")
                expiry = parse_date(value) if value else None
                if expiry is None or (expiry - today).days > days:
                    continue
                rows.append(
                    {
                        "application_id": app.id,
                        "full_name": app.full_name,
                        "doc_type": slot["doc_type"],
                        "doc_label": slot["label"],
                        "field": spec.label,
                        "date": expiry,
                        "days_left": (expiry - today).days,
                    }
                )
    return sorted(rows, key=lambda r: r["days_left"])


def to_csv(header: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")  # BOM: Excel then opens Cyrillic correctly


def expiring_csv(rows: list[dict]) -> bytes:
    header = ["Заявитель", "Документ", "Поле", "Дата", "Дней осталось"]
    return to_csv(
        header,
        [[r["full_name"], r["doc_label"], r["field"], r["date"].strftime("%d.%m.%Y"), r["days_left"]] for r in rows],
    )


def card_csv(app) -> bytes:
    """One row per field of every document slot (merged across files)."""
    rows = []
    for slot in doc_slots(app):
        for spec in DOC_TYPES[slot["doc_type"]].fields:
            f = slot["fields"][spec.name]
            rows.append(
                [
                    slot["label"],
                    spec.label,
                    f.get("value") or "",
                    "оператор" if f.get("edited_by") else "модель",
                    f"{f.get('confidence', 0):.2f}",
                    "; ".join(f.get("issues", [])),
                ]
            )
    return to_csv(["Документ", "Поле", "Значение", "Источник", "Уверенность", "Замечания"], rows)
