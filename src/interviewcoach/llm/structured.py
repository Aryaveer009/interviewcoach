"""Call an LLM for JSON and validate it against a Pydantic model, repairing on failure."""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..prompts import repair_user
from .base import LLMClient, LLMError, LLMRequest

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(raw: str) -> str:
    """Pull the JSON object out of a reply that may include code fences or chatter."""
    fenced = _FENCE.search(raw)
    if fenced:
        raw = fenced.group(1)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in model reply")
    return raw[start : end + 1]


def structured_call(llm: LLMClient, request: LLMRequest, model: type[T], *, retries: int = 2) -> T:
    """Validate the reply with Pydantic; on failure, show the model its error and retry."""
    current = request
    last_error = ""
    for _ in range(retries + 1):
        raw = llm.complete(current)
        try:
            return model.model_validate_json(extract_json(raw))
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            current = LLMRequest(
                task=request.task,
                system=request.system,
                user=repair_user(request.user, last_error),
                payload=request.payload,
            )
    raise LLMError(f"{model.__name__}: invalid output after {retries + 1} attempts: {last_error}")
