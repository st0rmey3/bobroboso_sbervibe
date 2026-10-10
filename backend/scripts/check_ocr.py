"""Check the configured OCR step with the same settings and code path the worker uses.

Run on the stand:
    docker compose cp "case_docs/СНИЛС Киселев Максим Васильевич.jpg" worker:/tmp/test.jpg
    docker compose exec worker python scripts/check_ocr.py /tmp/test.jpg
"""

import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.extraction import preprocess  # noqa: E402
from app.llm import get_ocr  # noqa: E402
from app.llm.base import bearer  # noqa: E402


def check_server() -> None:
    """Step 1: is the OCR server answering, and does it have our model?"""
    if settings.ocr_provider == "ollama":
        model = settings.ollama_ocr_model or settings.ollama_model
        url, headers, key = f"{settings.ollama_url}/api/tags", {}, "models"
    else:
        model = settings.ocr_model
        url, headers, key = f"{settings.ocr_base_url}/models", bearer(settings.ocr_api_key), "data"
    t0 = time.monotonic()
    try:
        r = httpx.get(url, headers=headers, timeout=20)
    except httpx.HTTPError as e:
        sys.exit(f"[1/2] FAIL: {url} не отвечает ({type(e).__name__}: {e})")
    items = r.json().get(key, []) if r.status_code == 200 else []
    names = [m.get("name") or m.get("id") for m in items]
    print(f"[1/2] {url} → HTTP {r.status_code} за {time.monotonic() - t0:.1f} с, модели: {names}")
    if model not in names:
        sys.exit(f"      FAIL: модели «{model}» нет на сервере — скачайте её или поправьте .env")


def main() -> None:
    print(f"OCR_PROVIDER={settings.ocr_provider}  LLM_PROVIDER={settings.llm_provider}")
    ocr = get_ocr()
    if ocr is None:
        sys.exit("OCR_PROVIDER=none — отдельного OCR нет, модель читает изображение сама. Нечего проверять.")
    if settings.ocr_provider != "tesseract":  # tesseract runs inside the container, no server to ask
        check_server()
    if len(sys.argv) < 2:
        print("[2/2] пропущено: передайте путь к файлу, чтобы проверить распознавание")
        return
    data = Path(sys.argv[1]).read_bytes()
    pages = preprocess.load(data, preprocess.sniff_mime(data) or "")
    t0 = time.monotonic()
    text = ocr.read_page(pages.images[0])
    print(f"[2/2] страница распознана за {time.monotonic() - t0:.1f} с, {len(text)} символов:\n{text[:800]}")


if __name__ == "__main__":
    main()
