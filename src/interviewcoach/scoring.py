"""Rubric scoring: send an answer to the LLM, get back a Pydantic-validated RubricScore."""

from __future__ import annotations

from .llm.base import LLMClient, LLMRequest
from .llm.structured import structured_call
from .models import DimensionScore, Question, RubricScore
from .prompts import SCORE_SYSTEM, score_user

NO_ANSWER = "No answer was given."


class RubricScorer:
    def __init__(self, llm: LLMClient, *, retries: int = 2) -> None:
        self.llm = llm
        self.retries = retries

    def score(self, question: Question, answer: str, resume_context: str = "") -> RubricScore:
        if not answer.strip():
            empty = DimensionScore(score=1, feedback=NO_ANSWER)
            return RubricScore(
                correctness=empty, depth=empty, clarity=empty, structure=empty, relevance=empty,
                overall_feedback="You skipped this question. Even a partial attempt earns credit.",
                sample_answer="Start with a one-line summary, then walk through your reasoning.",
            )
        request = LLMRequest(
            task="score",
            system=SCORE_SYSTEM,
            user=score_user(question, answer, resume_context),
            payload={"question": question.model_dump(mode="json"), "answer": answer},
        )
        return structured_call(self.llm, request, RubricScore, retries=self.retries)
