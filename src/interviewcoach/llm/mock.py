"""Deterministic offline "LLM" so the whole app and test-suite run with no key or network.

It does not read the prose prompts; it reads ``LLMRequest.payload`` and answers with JSON
that validates against the same Pydantic models a real model has to satisfy.
"""

from __future__ import annotations

import json

from ..knowledge import BEHAVIORAL, STAR_POINTS, technical_bank, to_expected
from ..models import Category, ExpectedPoint, Question, QuestionDraft
from .base import LLMClient, LLMError, LLMRequest
from .heuristic import heuristic_score

_FOLLOWUP_TEXT = {
    "correctness": "You didn't say much about: {missing}. Can you address that directly?",
    "depth": "Go one level deeper: why did you choose that approach over the obvious alternative, "
             "and what trade-off did it cost you?",
    "clarity": "Say that again in two sentences as if to a non-specialist, without hedging.",
    "structure": "Walk me through it step by step: what happened first, what next, and what was "
                 "the end result?",
    "relevance": "Let me bring it back to the question: how does your answer address {topic} "
                 "specifically?",
    "stretch": "Good. Now stretch it: how would your approach change at 100x the scale or if a "
               "requirement flipped, and what would you monitor to know it was failing?",
}


class MockLLM(LLMClient):
    def complete(self, request: LLMRequest) -> str:
        p = request.payload
        if request.task == "question":
            return self._question(p)
        if request.task == "followup":
            return self._followup(p)
        if request.task == "score":
            question = Question.model_validate(p["question"])
            return heuristic_score(question, str(p["answer"])).model_dump_json()
        raise LLMError(f"MockLLM does not support task {request.task!r}")

    # ------------------------------------------------------------------ questions

    def _question(self, p: dict) -> str:
        category = Category(p["category"])
        if category == Category.TECHNICAL:
            bank = technical_bank(p["topic"])
            if p.get("missing"):
                text = (
                    f"The role asks for {p['topic']}, which doesn't appear in your projects. "
                    f"{bank.question} If you haven't used it, tell me how you'd approach "
                    "learning it and what you already know."
                )
            else:
                text = bank.question
            draft = QuestionDraft(text=text, expected_points=to_expected(bank.points))
        elif category == Category.PROJECT:
            draft = self._project_question(p)
        else:
            topic = p["topic"]
            text = BEHAVIORAL.get(topic, f"Tell me about a time involving {topic}.")
            text += " Use the STAR structure: Situation, Task, Action, Result."
            draft = QuestionDraft(
                text=text,
                expected_points=[ExpectedPoint(description=d, keywords=list(k))
                                 for d, k in STAR_POINTS],
            )
        return draft.model_dump_json()

    @staticmethod
    def _project_question(p: dict) -> QuestionDraft:
        project = p["context"]["project"]
        bullet = p["context"].get("bullet", "")
        skills = p["context"].get("skills", [])
        lead = bullet[0].lower() + bullet[1:] if bullet else "worked on this project"
        lead = lead.rstrip(".")
        specific = [s for s in skills if s != "Python"]
        focus = (specific or skills or ["the main technology"])[0]
        text = (
            f"On your resume, for {project}, you say you {lead}. Walk me through it: what design "
            f"choices did you make (for example around {focus}), what was the hardest problem, "
            "and how did you know it worked?"
        )
        points = [
            ExpectedPoint(description=f"the design and why you made the choices you did around {focus}",
                          keywords=["because", "chose", "decided", "design", focus.lower()]),
            ExpectedPoint(description="a specific hard problem and how you solved it",
                          keywords=["challenge", "problem", "bug", "difficult", "hardest",
                                    "fixed", "solved"]),
            ExpectedPoint(description="how you verified it worked (tests, metrics, users)",
                          keywords=["test", "verified", "metric", "measured", "benchmark",
                                    "evaluat", "ci", "result"]),
            ExpectedPoint(description="what you would improve",
                          keywords=["improve", "next", "differently", "limitation",
                                    "would change", "future"]),
        ]
        return QuestionDraft(text=text, expected_points=points)

    # ------------------------------------------------------------------ follow-ups

    def _followup(self, p: dict) -> str:
        question = Question.model_validate(p["question"])
        kind = p["kind"]  # a rubric dimension, or "stretch"
        missing = ", ".join(list(p.get("missed", []))[:2])
        template = _FOLLOWUP_TEXT[kind if kind in _FOLLOWUP_TEXT else "depth"]
        text = template.format(topic=question.topic, missing=missing or "the core idea")
        if question.category == Category.BEHAVIORAL and kind in ("depth", "structure"):
            text = ("What was the concrete, measurable result of that, and what specifically "
                    "did *you* do versus the rest of the team?")
        pts = [ExpectedPoint(description=d.description, keywords=d.keywords)
               for d in question.expected_points][:2] or [
            ExpectedPoint(description="gives a specific, reasoned answer",
                          keywords=["because", "for example", "trade-off"])
        ]
        return json.dumps({"text": text, "expected_points": [pt.model_dump() for pt in pts]})
