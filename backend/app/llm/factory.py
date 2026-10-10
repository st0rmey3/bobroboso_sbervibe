from functools import lru_cache

from app.config import settings
from app.llm.base import LLMProvider


@lru_cache
def get_provider() -> LLMProvider:
    """The only place that knows concrete providers. Switch with LLM_PROVIDER=openai|ollama."""
    name = settings.llm_provider
    if name == "ollama":
        from app.llm.ollama import OllamaProvider

        return OllamaProvider()
    if name == "openai":
        from app.llm.openai_compat import OpenAICompatProvider

        return OpenAICompatProvider()
    raise ValueError(f"unknown LLM_PROVIDER: {name}")
