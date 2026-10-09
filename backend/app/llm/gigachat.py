"""GigaChat (Sber) via REST: OAuth token → upload page images → chat/completions with attachments.

UNTESTED in skeleton — verify against current docs (developers.sber.ru/docs/ru/gigachat/api) when keys arrive.
"""

import time
import uuid
from collections.abc import Sequence

import httpx

from app.config import settings
from app.llm.base import LLMError, LLMProvider, LLMResponse, parse_json, schema_hint

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1"


class GigaChatProvider(LLMProvider):
    name = "gigachat"

    def __init__(self) -> None:
        self.model = settings.gigachat_model
        self._http = httpx.Client(timeout=settings.llm_timeout_s, verify=settings.gigachat_verify_ssl)
        self._token: str | None = None
        self._token_exp = 0.0

    def _auth(self) -> dict:
        if not self._token or time.time() > self._token_exp - 60:
            try:
                r = self._http.post(
                    OAUTH_URL,
                    headers={"Authorization": f"Basic {settings.gigachat_credentials}", "RqUID": str(uuid.uuid4())},
                    data={"scope": settings.gigachat_scope},
                )
            except httpx.HTTPError as e:
                raise LLMError(f"gigachat oauth unreachable: {e}") from e
            if r.status_code >= 400:
                raise LLMError(f"gigachat oauth {r.status_code}", retryable=r.status_code >= 500)
            body = r.json()
            self._token, self._token_exp = body["access_token"], body["expires_at"] / 1000
        return {"Authorization": f"Bearer {self._token}"}

    def _upload(self, img: bytes) -> str:
        r = self._http.post(
            f"{API_URL}/files",
            headers=self._auth(),
            files={"file": ("page.jpg", img, "image/jpeg")},
            data={"purpose": "general"},
        )
        if r.status_code >= 400:
            raise LLMError(f"gigachat upload {r.status_code}: {r.text[:300]}", retryable=r.status_code >= 500)
        return r.json()["id"]

    def complete_json(self, *, system: str, prompt: str, schema: dict, images: Sequence[bytes] = ()) -> LLMResponse:
        t0 = time.monotonic()
        try:
            attachments = [self._upload(i) for i in images]
            r = self._http.post(
                f"{API_URL}/chat/completions",
                headers=self._auth(),
                json={
                    "model": self.model,
                    "temperature": 0.01,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"{prompt}\n\n{schema_hint(schema)}", "attachments": attachments},
                    ],
                },
            )
        except httpx.HTTPError as e:
            raise LLMError(f"gigachat unreachable: {e}") from e
        if r.status_code >= 400:
            raise LLMError(
                f"gigachat {r.status_code}: {r.text[:300]}", retryable=r.status_code in (429,) or r.status_code >= 500
            )
        data = parse_json(r.json()["choices"][0]["message"]["content"])
        # TODO(T-007): delete uploaded files after use (personal data).
        return LLMResponse(data, self.name, self.model, int((time.monotonic() - t0) * 1000))
