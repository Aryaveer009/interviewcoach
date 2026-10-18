"""Runtime configuration, read from environment variables (see ``.env.example``)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

AUTHOR_NAME = "Aryaveer Mankotia"
AUTHOR_URL = "https://github.com/Aryaveer009"


@dataclass(frozen=True)
class Settings:
    provider: str  # "mock" | "openai"  (openai == any OpenAI-compatible endpoint)
    api_key: str | None
    base_url: str | None
    model: str
    db_path: Path
    stt_backend: str  # "api" | "local" | "off"
    whisper_model: str
    stt_api_model: str

    @property
    def is_mock(self) -> bool:
        return self.provider == "mock"

    @property
    def llm_label(self) -> str:
        return "mock (offline heuristic)" if self.is_mock else f"{self.model}"

    @classmethod
    def from_env(cls, *, load_dotenv_file: bool = True) -> Settings:
        if load_dotenv_file:
            load_dotenv()
        key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or None
        provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        if provider in ("", "auto"):
            provider = "openai" if key else "mock"
        if provider not in ("mock", "openai"):
            raise ValueError(f"LLM_PROVIDER must be 'mock' or 'openai', got {provider!r}")
        if provider == "openai" and not key and not os.getenv("LLM_BASE_URL"):
            raise ValueError("LLM_PROVIDER=openai needs LLM_API_KEY (or a local LLM_BASE_URL)")
        default_db = Path.home() / ".interviewcoach" / "interviewcoach.db"
        return cls(
            provider=provider,
            api_key=key,
            base_url=os.getenv("LLM_BASE_URL") or None,
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            db_path=Path(os.getenv("INTERVIEWCOACH_DB", str(default_db))).expanduser(),
            stt_backend=os.getenv("STT_BACKEND", "off").strip().lower(),
            whisper_model=os.getenv("WHISPER_MODEL", "base.en"),
            stt_api_model=os.getenv("STT_API_MODEL", "whisper-1"),
        )
