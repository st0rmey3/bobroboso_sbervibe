"""Measure extraction quality on a labeled set WITHOUT touching the DB/queue.

Layout (data/ is git-ignored — personal data):
    data/open/<name>.<pdf|jpg|png>
    data/open/<name>.json   {"doc_type": "passport_ru", "fields": {"last_name": "…", …}}

Run: docker compose exec worker python scripts/eval_extraction.py data/open
TODO(T-008): per-field accuracy table, confusion of doc types, latency; compare providers via LLM_PROVIDER.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.extraction import doctypes, preprocess, prompts  # noqa: E402
from app.llm import get_ocr, get_provider  # noqa: E402


def norm(v: str | None) -> str:
    return " ".join((v or "").lower().replace("ё", "е").split())


def main(folder: str) -> None:
    llm, ocr = get_provider(), get_ocr()
    total = hits = type_ok = n = 0
    for label in sorted(Path(folder).glob("*.json")):
        expected = json.loads(label.read_text())
        src = next(p for p in label.parent.glob(label.stem + ".*") if p.suffix != ".json")
        data = src.read_bytes()
        pages = preprocess.load(data, preprocess.sniff_mime(data) or "")
        text, images = pages.text, pages.images
        if ocr is not None:  # same order as the pipeline: OCR text → LLM without images
            text, images = "\n\n".join([pages.text, *(ocr.read_page(i) for i in pages.images)]), []
        cls = llm.complete_json(
            system=prompts.SYSTEM,
            prompt=prompts.classify_prompt(text),
            schema=doctypes.classification_schema(),
            images=images,
        )
        n += 1
        got_type = cls.data.get("doc_type")
        type_ok += got_type == expected["doc_type"]
        dt = doctypes.DOC_TYPES.get(expected["doc_type"])
        if dt is None:
            continue
        ext = llm.complete_json(
            system=prompts.SYSTEM,
            prompt=prompts.extract_prompt(dt, text),
            schema=doctypes.extraction_schema(dt),
            images=images,
        )
        got = doctypes.validate(dt, ext.data.get("fields") or {})
        for name, want in expected["fields"].items():
            total += 1
            ok = norm(got.get(name, {}).get("value")) == norm(want)
            hits += ok
            if not ok:
                print(f"  {src.name}:{name}: want={want!r} got={got.get(name, {}).get('value')!r}")
    print(f"files={n} type_acc={type_ok / max(n, 1):.2%} field_acc={hits / max(total, 1):.2%} ({llm.name}/{llm.model})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/open")
