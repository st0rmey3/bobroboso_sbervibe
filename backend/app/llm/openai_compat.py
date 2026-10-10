"""Any OpenAI-compatible Chat Completions API: OpenAI, DeepSeek, OpenRouter, vLLM, LM Studio."""

import base64
import time
from collections.abc import Sequence

import httpx

from app.config import settings
from app.llm.base import LLMError, LLMProvider, LLMResponse, bearer, parse_json, schema_hint


class OpenAICompatProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        self.model = settings.openai_model
        self._client = httpx.Client(
            base_url=settings.openai_base_url,
            timeout=settings.llm_timeout_s,
            headers=bearer(settings.openai_api_key),
        )

    def complete_json(self, *, system: str, prompt: str, schema: dict, images: Sequence[bytes] = ()) -> LLMResponse:
        content: list[dict] = [{"type": "text", "text": f"{prompt}\n\n{schema_hint(schema)}"}]
        for img in images:
            b64 = base64.b64encode(img).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
        }
        if settings.openai_disable_thinking:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        t0 = time.monotonic()
        try:
            r = self._client.post("/chat/completions", json=body)
        except httpx.HTTPError as e:
            raise LLMError(f"openai-compatible API unreachable: {e}") from e
        if r.status_code >= 400:
            retryable = r.status_code == 429 or r.status_code >= 500
            raise LLMError(f"openai-compatible {r.status_code}: {r.text[:300]}", retryable=retryable)
        data = parse_json(r.json()["choices"][0]["message"]["content"])
        return LLMResponse(data, self.name, self.model, int((time.monotonic() - t0) * 1000))
