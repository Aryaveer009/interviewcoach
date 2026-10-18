from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from interviewcoach.llm.base import LLMClient, LLMError, LLMRequest
from interviewcoach.llm.structured import extract_json
from interviewcoach.models import (
    Category,
    DimensionScore,
    ExpectedPoint,
    Question,
    RubricScore,
)
from interviewcoach.scoring import RubricScorer


def valid_score_dict(score: int = 4) -> dict:
    def dim() -> dict:
        return {"score": score, "feedback": "Specific feedback."}

    return {"correctness": dim(), "depth": dim(), "clarity": dim(), "structure": dim(),
            "relevance": dim(), "overall_feedback": "Solid.",
            "sample_answer": "A stronger answer would explain the mechanism and an example."}


def question() -> Question:
    return Question(category=Category.TECHNICAL, text="Explain what a Python generator is.",
                    topic="Python",
                    expected_points=[ExpectedPoint(description="lazy values",
                                                   keywords=["lazy", "yield"])])


class ScriptedLLM(LLMClient):
    def __init__(self, replies: list[str]) -> None:
        self.replies, self.calls = replies, []

    def complete(self, request: LLMRequest) -> str:
        self.calls.append(request)
        return self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]


@pytest.mark.parametrize("bad", [0, 6, -1])
def test_dimension_score_bounds(bad):
    with pytest.raises(ValidationError):
        DimensionScore(score=bad, feedback="ok feedback")


def test_rubric_rejects_missing_dimension_and_short_sample():
    data = valid_score_dict()
    del data["depth"]
    with pytest.raises(ValidationError):
        RubricScore.model_validate(data)
    data = valid_score_dict()
    data["sample_answer"] = "too short"
    with pytest.raises(ValidationError):
        RubricScore.model_validate(data)


def test_rubric_overall_and_weakest_dimension():
    data = valid_score_dict(4)
    data["clarity"]["score"] = 2
    data["depth"]["score"] = 2
    score = RubricScore.model_validate(data)
    assert score.overall == 3.2
    assert score.weakest_dimension() == "depth"  # tie broken by rubric order
    assert set(score.dimension_scores()) == {"correctness", "depth", "clarity", "structure",
                                             "relevance"}


def test_extract_json_handles_fences_and_chatter():
    assert json.loads(extract_json('Sure!\n```json\n{"a": 1}\n```\nHope this helps')) == {"a": 1}
    assert json.loads(extract_json('prefix {"a": {"b": 2}} suffix')) == {"a": {"b": 2}}
    with pytest.raises(ValueError):
        extract_json("no json here")


def test_scorer_retries_invalid_json_then_succeeds():
    llm = ScriptedLLM(["not json at all", json.dumps({**valid_score_dict(), "depth": {
        "score": 9, "feedback": "x ok"}}), json.dumps(valid_score_dict(5))])
    result = RubricScorer(llm).score(question(), "A generator yields lazily.")
    assert result.overall == 5.0
    assert len(llm.calls) == 3
    assert "invalid" in llm.calls[1].user  # the model is shown its validation error


def test_scorer_raises_after_exhausting_retries():
    llm = ScriptedLLM(["garbage"])
    with pytest.raises(LLMError, match="invalid output after 3 attempts"):
        RubricScorer(llm, retries=2).score(question(), "answer")
    assert len(llm.calls) == 3


def test_empty_answer_scores_minimum_without_calling_llm():
    llm = ScriptedLLM(["should not be used"])
    result = RubricScorer(llm).score(question(), "   ")
    assert result.overall == 1.0 and llm.calls == []


def test_structured_call_accepts_fenced_reply():
    llm = ScriptedLLM(["```json\n" + json.dumps(valid_score_dict(3)) + "\n```"])
    assert RubricScorer(llm).score(question(), "text").overall == 3.0


def test_mock_llm_scores_are_deterministic_and_valid(llm):
    q = question()
    a = RubricScorer(llm).score(q, "A generator yields values lazily, for example in a loop.")
    b = RubricScorer(llm).score(q, "A generator yields values lazily, for example in a loop.")
    assert a == b
    assert all(1 <= s <= 5 for s in a.dimension_scores().values())


def test_mock_scores_rise_with_better_answers(llm):
    q = question()
    weak = RubricScorer(llm).score(q, "idk")
    strong = RubricScorer(llm).score(
        q, "A generator produces values lazily using yield, so memory stays small because "
           "nothing is stored. For example, reading a large file line by line. First it "
           "pauses at yield, then resumes. The trade-off is that you can only iterate once.")
    assert strong.overall > weak.overall
