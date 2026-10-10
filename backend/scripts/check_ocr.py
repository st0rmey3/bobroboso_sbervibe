"""Check the OCR service with the same settings and code path the worker uses.

Run:  docker compose exec worker python scripts/check_ocr.py [path/to/image_or_pdf]
      (or locally from backend/:  OCR_BASE_URL=... python scripts/check_ocr.py file.jpg)
"""

import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.extraction import preprocess  # noqa: E402
from app.llm.base import bearer  # noqa: E402
from app.llm.ocr import OlmOcrProvider  # noqa: E402


def main() -> None:
    print(f"OCR_PROVIDER={settings.ocr_provider}  OCR_BASE_URL={settings.ocr_base_url}  OCR_MODEL={settings.ocr_model}")

    # 1. Is the server answering, and does it serve our model name?
    t0 = time.monotonic()
    try:
        r = httpx.get(
            f"{settings.ocr_base_url}/models",
            headers=bearer(settings.ocr_api_key),
            timeout=20,
        )
    except httpx.HTTPError as e:
        sys.exit(f"[1/2] FAIL: server not answering /models ({type(e).__name__}: {e})")
    models = [m["id"] for m in r.json().get("data", [])] if r.status_code == 200 else []
    print(f"[1/2] /models → HTTP {r.status_code} in {time.monotonic() - t0:.1f}s, models: {models}")
    if settings.ocr_model not in models:
        sys.exit(f"      FAIL: OCR_MODEL '{settings.ocr_model}' is not served — set OCR_MODEL to one of {models}")

    # 2. Recognize one page through our provider (same code as the worker).
    if len(sys.argv) < 2:
        print("[2/2] skipped: pass a file to test recognition")
        return
    data = Path(sys.argv[1]).read_bytes()
    pages = preprocess.load(data, preprocess.sniff_mime(data) or "")
    t0 = time.monotonic()
    text = OlmOcrProvider().read_page(pages.images[0])
    print(f"[2/2] recognized page 1 in {time.monotonic() - t0:.1f}s, {len(text)} chars:\n{text[:800]}")


if __name__ == "__main__":
    main()
