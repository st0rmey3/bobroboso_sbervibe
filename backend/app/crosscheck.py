"""Cross-document consistency: one person's documents must agree with each other and with the typed name.

Names are compared after transliteration to Latin (passport RF in Cyrillic vs Belarus passport in Latin is the same
person), ignoring case, «ё», punctuation and word order. Results are warnings for the operator — never auto-reject.
"""

from difflib import SequenceMatcher

_TRANSLIT = {
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E", "Ж": "ZH", "З": "Z", "И": "I", "Й": "I",
    "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U", "Ф": "F",
    "Х": "KH", "Ц": "TS", "Ч": "CH", "Ш": "SH", "Щ": "SHCH", "Ъ": "", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "YU",
    "Я": "YA", "Ў": "U", "І": "I", "Қ": "K", "Ғ": "G", "Ҳ": "H", "Ң": "N", "Ү": "U", "Ө": "O",
}  # fmt: skip
# Spelling variants that differ between transliteration systems.
_SIMPLIFY = [("KH", "H"), ("Y", "I"), ("J", "I"), ("W", "V"), ("TS", "C"), ("Q", "K")]
NAME_SIMILARITY = 0.75  # SIDORENKO vs SIDARENKA (Belarusian Latin) = 0.78


def _tokens(name: str) -> list[str]:
    latin = "".join(_TRANSLIT.get(ch, ch) for ch in name.upper())
    for a, b in _SIMPLIFY:
        latin = latin.replace(a, b)
    words = "".join(ch if ch.isalpha() else " " for ch in latin).split()
    return [w for w in words if len(w) > 1]


def _same_word(a: str, b: str) -> bool:
    return a == b or SequenceMatcher(None, a, b).ratio() >= NAME_SIMILARITY


def same_person(name_a: str, name_b: str) -> bool:
    """True if the shorter name's words all appear in the longer one (patronymic may be missing on one document)."""
    a, b = _tokens(name_a), _tokens(name_b)
    if not a or not b:
        return True  # nothing to compare
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    unused = list(long_)
    for word in short:  # one-to-one: «IVANOV IVAN» must not match «PETROV IVAN» via IVANOV≈IVAN
        match = next((other for other in unused if _same_word(word, other)), None)
        if match is None:
            return False
        unused.remove(match)
    return True


def _values(slots: list[dict], field: str) -> list[tuple[str, str]]:
    """(document label, value) for every document type that has this field filled."""
    found = []
    for slot in slots:
        value = slot["fields"].get(field, {}).get("value")
        if value:
            found.append((slot["label"], value))
    return found


def cross_checks(full_name: str, slots: list[dict]) -> list[str]:
    """Warnings for one application. `slots` come from applications.doc_slots (merged fields per document type)."""
    names = _values(slots, "full_name")
    births = _values(slots, "birth_date")
    warnings = []
    for label, name in names:
        if not same_person(full_name, name):
            warnings.append(f"ФИО в заявке «{full_name}» не совпадает с документом «{name}» ({label})")
    for i, (label_a, name_a) in enumerate(names):
        for label_b, name_b in names[i + 1 :]:
            if not same_person(name_a, name_b):
                warnings.append(f"ФИО различается: «{name_a}» ({label_a}) и «{name_b}» ({label_b})")
    if len({date for _, date in births}) > 1:
        listed = ", ".join(f"{date} ({label})" for label, date in births)
        warnings.append(f"Дата рождения различается: {listed}")
    return warnings
