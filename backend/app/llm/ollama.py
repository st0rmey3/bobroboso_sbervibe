"""Local provider: Ollama (native /api/chat with structured output via `format`)."""

import base64
import time
from collections.abc import Sequence

import httpx

from app.config import settings
from app.llm.base import LLMError, LLMProvider, LLMResponse, parse_json


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.model = settings.ollama_model
        self._client = httpx.Client(base_url=settings.ollama_url, timeout=settings.llm_timeout_s)

    def complete_json(self, *, system: str, prompt: str, schema: dict, images: Sequence[bytes] = ()) -> LLMResponse:
        body = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0},
            "keep_alive": "30m",  # keep the model in GPU memory between documents
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt, "images": [base64.b64encode(i).decode() for i in images]},
            ],
        }
        t0 = time.monotonic()
        try:
            r = self._client.post("/api/chat", json=body)
        except httpx.HTTPError as e:
            raise LLMError(f"ollama unreachable: {e}") from e
        if r.status_code >= 400:
            raise LLMError(f"ollama {r.status_code}: {r.text[:300]}", retryable=r.status_code >= 500)
        data = parse_json(r.json()["message"]["content"])
        return LLMResponse(data, self.name, self.model, int((time.monotonic() - t0) * 1000))
