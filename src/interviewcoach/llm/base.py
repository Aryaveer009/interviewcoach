"""LLM abstraction: one tiny interface so the agent never cares which provider is behind it."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

Task = Literal["question", "followup", "score"]


class LLMError(RuntimeError):
    """Raised when the provider fails or returns something unusable after retries."""


@dataclass
class LLMRequest:
    """A request for JSON output.

    ``system``/``user`` are the prompts sent to a real model. ``payload`` carries the same
    information as structured data, which the offline mock uses (it never reads prose).
    """

    task: Task
    system: str
    user: str
    payload: dict[str, Any] = field(default_factory=dict)


class LLMClient(ABC):
    @abstractmethod
    def complete(self, request: LLMRequest) -> str:
        """Return the model's raw text, expected to contain one JSON object."""
