"""Model prompts (case 5.3: prompts live in the repo). Generic per document type — no sample-specific values."""

from app.extraction.doctypes import DOC_TYPES, DocType

SYSTEM = (
    "Ты — система разбора документов кадрового агентства. Используй только то, что есть на изображении "
    "или в распознанном тексте документа. Ничего не придумывай: если значение не видно или нечитаемо — "
    "value=null и низкая confidence. confidence — число от 0 до 1: насколько ты уверен в прочтении. "
    "Даты возвращай в формате ДД.ММ.ГГГГ. Отвечай только JSON."
)


def _source(text: str) -> str:
    if text.strip():
        return f"\n\nРаспознанный текст документа:\n<<<\n{text[:8000]}\n>>>"
    return "\n\nДокумент приложен изображениями."


def classify_prompt(text: str) -> str:
    types = "\n".join(f"- {dt.code}: {dt.label}. {dt.description}" for dt in DOC_TYPES.values())
    return (
        "Определи вид документа. Возможные виды:\n"
        f"{types}\n- unknown: ни один из перечисленных.\n"
        "readable=false, если документ нельзя прочитать (размыт, обрезан, засвечен, пустая страница); "
        "тогда в reason коротко объясни по-русски, что не так." + _source(text)
    )


def extract_prompt(dt: DocType, text: str) -> str:
    lines = []
    for f in dt.fields:
        line = f"- {f.name}: {f.label}"
        if f.kind == "date":
            line += " (дата)"
        if f.hint:
            line += f"; {f.hint}"
        lines.append(line)
    return f"Документ: {dt.label}. Извлеки поля:\n" + "\n".join(lines) + _source(text)
