"""Prompts are generic per document type — no sample-specific values (see AGENTS.md §1)."""

from app.extraction.doctypes import DOC_TYPES, DocType

SYSTEM = (
    "Ты — система распознавания документов отдела кадров. Работаешь только с тем, что видно на изображении. "
    "Ничего не придумывай: если значения не видно или оно нечитаемо — value=null и низкая confidence. "
    "confidence — число 0..1, насколько ты уверен в прочтении."
)


def classify_prompt(text_layer: str) -> str:
    types = "\n".join(f"- {dt.code}: {dt.label}. {dt.description}" for dt in DOC_TYPES.values())
    tail = f"\n\nТекстовый слой файла (может быть пустым):\n{text_layer[:3000]}" if text_layer else ""
    return (
        "Определи тип документа на изображениях. Возможные типы:\n"
        f"{types}\n- unknown: ни один из перечисленных.\n"
        "readable=false, если документ нельзя прочитать (размыт, обрезан, засвечен, пустой)." + tail
    )


def extract_prompt(dt: DocType, text_layer: str) -> str:
    fields = "\n".join(
        f"- {f.name}: {f.label}"
        + (" (дата, формат ДД.ММ.ГГГГ)" if f.kind == "date" else "")
        + (f"; {f.hint}" if f.hint else "")
        for f in dt.fields
    )
    tail = f"\n\nТекстовый слой файла:\n{text_layer[:6000]}" if text_layer else ""
    return f"Документ: {dt.label}. Извлеки поля:\n{fields}" + tail
