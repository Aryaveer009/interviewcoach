from __future__ import annotations

from ..config import Settings
from .base import LLMClient, LLMError, LLMRequest
from .mock import MockLLM
from .openai_client import OpenAICompatClient


def get_llm(settings: Settings) -> LLMClient:
    """Build the client selected by ``LLM_PROVIDER`` (mock needs no key and no network)."""
    if settings.is_mock:
        return MockLLM()
    return OpenAICompatClient(settings.model, settings.api_key, settings.base_url)


__all__ = ["LLMClient", "LLMError", "LLMRequest", "MockLLM", "OpenAICompatClient", "get_llm"]
