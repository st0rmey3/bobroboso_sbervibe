"""OCR step: page image → plain text. Part of the model layer (it is a model call too).

OCR_PROVIDER=olmocr — olmOCR-2 served by vLLM behind an OpenAI-compatible API (Sber's server or self-hosted).
OCR_PROVIDER=ollama — local OCR: a vision model in Ollama transcribes the page (nothing leaves the machine).
OCR_PROVIDER=none   — no separate OCR: the LLM provider reads page images itself (vision model, e.g. local Ollama).
"""

import base64
from abc import ABC, abstractmethod

import httpx

from app.config import settings
from app.llm.base import LLMError, bearer

# olmOCR is fine-tuned on this exact prompt (olmocr.prompts.build_no_anchoring_v4_yaml_prompt) — keep it verbatim.
OLMOCR_PROMPT = (
    "Attached is one page of a document that you must process. "
    "Just return the plain text representation of this document as if you were reading it naturally. "
    "Convert equations to LateX and tables to HTML.\n"
    "If there are any figures or charts, label them with the following markdown syntax "
    "![Alt text describing the contents of the figure](page_startx_starty_width_height.png)\n"
    "Return your output as markdown, with a front matter section on top specifying values for the "
    "primary_language, is_rotation_valid, rotation_correction, is_table, and is_diagram parameters."
)


class OcrProvider(ABC):
    name: str

    @abstractmethod
    def read_page(self, image: bytes) -> str:
        """Return the page text. Raises LLMError on failure."""


def strip_front_matter(content: str) -> str:
    text = content.strip()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].strip()
    return text


class OlmOcrProvider(OcrProvider):
    name = "olmocr"

    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=settings.ocr_base_url,
            timeout=settings.ocr_timeout_s,
            headers=bearer(settings.ocr_api_key),
        )

    def read_page(self, image: bytes) -> str:
        b64 = base64.b64encode(image).decode()
        body = {
            "model": settings.ocr_model,
            "temperature": 0.0,
            "max_tokens": settings.ocr_max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": OLMOCR_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }
            ],
        }
        try:
            r = self._client.post("/chat/completions", json=body)
        except httpx.HTTPError as e:
            raise LLMError(f"OCR unreachable: {e}") from e
        if r.status_code >= 400:
            retryable = r.status_code == 429 or r.status_code >= 500
            raise LLMError(f"OCR {r.status_code}: {r.text[:300]}", retryable=retryable)
        return strip_front_matter(r.json()["choices"][0]["message"]["content"] or "")


LOCAL_OCR_PROMPT = (
    "Перепиши весь текст с изображения документа построчно, как он напечатан, сохраняя цифры, даты и буквы "
    "(кириллицу и латиницу). Ничего не добавляй и не объясняй. Нечитаемые места замени на [?]."
)


class OllamaOcrProvider(OcrProvider):
    name = "ollama-ocr"

    def __init__(self) -> None:
        self.model = settings.ollama_ocr_model or settings.ollama_model
        self._client = httpx.Client(base_url=settings.ollama_url, timeout=settings.ocr_timeout_s)

    def read_page(self, image: bytes) -> str:
        body = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0},
            "messages": [{"role": "user", "content": LOCAL_OCR_PROMPT, "images": [base64.b64encode(image).decode()]}],
        }
        try:
            r = self._client.post("/api/chat", json=body)
        except httpx.HTTPError as e:
            raise LLMError(f"local OCR (ollama) unreachable: {e}") from e
        if r.status_code >= 400:
            raise LLMError(f"local OCR (ollama) {r.status_code}: {r.text[:300]}", retryable=r.status_code >= 500)
        return r.json()["message"]["content"].strip()


def get_ocr() -> OcrProvider | None:
    if settings.ocr_provider == "olmocr":
        return OlmOcrProvider()
    if settings.ocr_provider == "ollama":
        return OllamaOcrProvider()
    if settings.ocr_provider == "none":
        return None
    raise ValueError(f"unknown OCR_PROVIDER: {settings.ocr_provider}")
