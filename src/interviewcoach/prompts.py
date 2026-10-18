"""Prompts for a real LLM. The mock ignores these and reads ``LLMRequest.payload`` instead."""

from __future__ import annotations

import json

from .models import Question, RubricScore

QUESTION_SYSTEM = """You are a senior engineer conducting a realistic job interview.
Write ONE interview question and the points a strong answer should cover.
Return ONLY a JSON object: {"text": str, "expected_points": [{"description": str, "keywords": [str]}]}
- 3 to 5 expected points; keywords are short lowercase stems that would appear in a good answer.
- Be specific to the candidate's resume and the job when context is given. No preamble."""

FOLLOWUP_SYSTEM = """You are a senior engineer interviewing a candidate. Given the previous
question, the candidate's answer and where it was weak, write ONE short follow-up question.
If kind is "stretch" the answer was strong: push on trade-offs, scale or failure modes.
Otherwise probe the weak dimension named by kind. Return ONLY JSON:
{"text": str, "expected_points": [{"description": str, "keywords": [str]}]}"""

SCORE_SYSTEM = """You are a strict but fair interview evaluator. Score the candidate's answer
on five dimensions, each an integer 1-5, using these anchors:
- correctness: 1 = wrong or no answer, 3 = partly right with gaps, 5 = accurate and complete.
- depth: 1 = surface statement, 3 = some detail, 5 = specifics, trade-offs, examples.
- clarity: 1 = confusing/rambling, 3 = understandable, 5 = concise and unambiguous.
- structure: 1 = disorganised, 3 = some order, 5 = clear flow (for behavioural: full STAR).
- relevance: 1 = off-topic, 3 = partly on topic, 5 = fully addresses the question.
Do not reward length or buzzwords; reward accuracy and specifics. Do not invent facts about
the candidate. Return ONLY a JSON object with exactly these keys:
{"correctness": {"score": int, "feedback": str}, "depth": {...}, "clarity": {...},
 "structure": {...}, "relevance": {...}, "overall_feedback": str, "sample_answer": str}
Each feedback must be specific to THIS answer. sample_answer is a stronger answer (80-150
words) the candidate could give, consistent with their resume context."""


def question_user(slot: dict) -> str:
    return "Write the question for this slot:\n" + json.dumps(slot, indent=2)


def followup_user(question: Question, answer: str, kind: str, weakest_feedback: str) -> str:
    return json.dumps(
        {
            "previous_question": question.text,
            "candidate_answer": answer,
            "kind": kind,
            "weak_area_feedback": weakest_feedback,
        },
        indent=2,
    )


def score_user(question: Question, answer: str, resume_context: str) -> str:
    return json.dumps(
        {
            "category": question.category.value,
            "question": question.text,
            "expected_points": [p.description for p in question.expected_points],
            "resume_context": resume_context[:1500],
            "candidate_answer": answer,
        },
        indent=2,
    )


def repair_user(original: str, error: str) -> str:
    return (
        original
        + "\n\nYour previous reply was invalid:\n"
        + error[:600]
        + "\nReturn ONLY the corrected JSON object."
    )


SCHEMA_HINT = RubricScore.model_json_schema()
