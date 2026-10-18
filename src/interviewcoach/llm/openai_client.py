"""Client for any OpenAI-compatible chat-completions endpoint (OpenAI, Groq, Ollama, vLLM...)."""

from __future__ import annotations

from typing import Any

from .base import LLMClient, LLMError, LLMRequest


class OpenAICompatClient(LLMClient):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        client: Any | None = None,
        temperature: float = 0.3,
        timeout: float = 60.0,
    ) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key or "not-needed", base_url=base_url, timeout=timeout)
        self._client: Any = client
        self.model = model
        self.temperature = temperature

    def complete(self, request: LLMRequest) -> str:
        messages = [
            {"role": "system", "content": request.system},
            {"role": "user", "content": request.user},
        ]
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            # Some compatible servers reject response_format; retry once without it.
            if "response_format" not in str(exc).lower():
                raise LLMError(f"LLM request failed: {exc}") from exc
            try:
                resp = self._client.chat.completions.create(
                    model=self.model, messages=messages, temperature=self.temperature
                )
            except Exception as exc2:
                raise LLMError(f"LLM request failed: {exc2}") from exc2
        content = resp.choices[0].message.content
        if not content:
            raise LLMError("LLM returned an empty response")
        return str(content)
