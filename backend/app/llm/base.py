"""Provider-agnostic interface. The rest of the app only knows LLMProvider / LLMError / get_provider()."""

import json
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass


class LLMError(Exception):
    """Model call failed. retryable=True → the worker retries the job with backoff."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


@dataclass
class LLMResponse:
    data: dict
    provider: str
    model: str
    latency_ms: int


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def complete_json(self, *, system: str, prompt: str, schema: dict, images: Sequence[bytes] = ()) -> LLMResponse:
        """Send a prompt (+ page images as JPEG/PNG bytes), return parsed JSON matching `schema`."""


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json(raw: str) -> dict:
    """Models sometimes wrap JSON in ``` fences or add text around it."""
    text = _FENCE.sub("", raw.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise LLMError("model returned no JSON object")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise LLMError(f"model returned invalid JSON: {e}") from e


def schema_hint(schema: dict) -> str:
    """For providers without native structured output: put the schema into the prompt."""
    return "Ответь строго одним JSON-объектом по этой JSON Schema, без пояснений:\n" + json.dumps(
        schema, ensure_ascii=False
    )
