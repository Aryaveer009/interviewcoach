"""The interview agent: plan -> ask -> score -> (adaptive follow-up) -> persist.

The *policy* (what to ask about, when to follow up, how to follow up) is plain Python and
fully deterministic. The LLM only phrases questions and judges answers, so behaviour is
easy to test and to explain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .db import Database
from .llm.base import LLMClient, LLMRequest
from .llm.heuristic import coverage
from .llm.structured import structured_call
from .models import (
    Category,
    GapReport,
    GapStatus,
    JobDescription,
    Question,
    QuestionDraft,
    ResumeProfile,
    RubricScore,
)
from .prompts import FOLLOWUP_SYSTEM, QUESTION_SYSTEM, followup_user, question_user
from .scoring import RubricScorer
from .skills import count_mentions, extract_skills

STRETCH_AT = 4.5  # overall >= this: the answer was strong, push harder
PROBE_BELOW = 4.0  # overall < this: probe the weakest dimension
BEHAVIORAL_ORDER = ("learning quickly", "conflict", "failure", "deadline pressure", "ownership",
                    "feedback")


@dataclass
class Slot:
    category: Category
    topic: str
    source: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    missing: bool = False

    def payload(self) -> dict[str, Any]:
        return {"category": self.category.value, "topic": self.topic, "source": self.source,
                "context": self.context, "missing": self.missing}


# --------------------------------------------------------------------------- planning


def build_plan(
    profile: ResumeProfile,
    jd: JobDescription,
    gap: GapReport,
    *,
    n_technical: int = 3,
    n_project: int = 2,
    n_behavioral: int = 2,
) -> list[Slot]:
    """Choose what to ask about. Order: project warm-up, technical, behavioural."""
    wanted = {i.skill for i in gap.items}

    def rank(skills: list[str]) -> list[str]:
        # most-mentioned JD skills first; stable for ties
        return sorted(skills, key=lambda s: -count_mentions(jd.raw_text, s))

    # --- technical: verify claimed skills the JD cares about most, plus one gap probe
    claimed = rank([i.skill for i in gap.items
                    if i.importance == "required" and i.status != GapStatus.MISSING])
    missing_req = rank([i.skill for i in gap.items
                        if i.importance == "required" and i.status == GapStatus.MISSING])
    missing_pref = rank([i.skill for i in gap.items
                         if i.importance == "preferred" and i.status == GapStatus.MISSING])
    probe = (missing_req or missing_pref)[:1] if n_technical > 0 else []
    tech_topics = claimed[: max(0, n_technical - len(probe))]
    if len(tech_topics) + len(probe) < n_technical:  # not enough claimed: add other skills
        extras = [s for s in rank(list(wanted)) if s not in tech_topics and s not in probe]
        tech_topics += extras[: n_technical - len(tech_topics) - len(probe)]
    technical = [Slot(Category.TECHNICAL, t, source="job description") for t in tech_topics]
    technical += [Slot(Category.TECHNICAL, t, source="skills gap", missing=True) for t in probe]

    # --- project deep-dives: projects whose skills overlap the JD most
    def overlap(p: Any) -> int:
        return len(set(p.skills) & wanted)

    projects = sorted(profile.projects, key=lambda p: -overlap(p))[:n_project]
    project_slots = []
    for p in projects:
        bullet = max(p.bullets, key=lambda b: (len(re.findall(r"\d", b)), len(b)), default="")
        project_slots.append(
            Slot(Category.PROJECT, p.name, source="resume",
                 context={"project": p.name, "bullet": bullet,
                          "skills": _bullet_first(bullet, p.skills)})
        )

    # --- behavioural
    order = list(BEHAVIORAL_ORDER)
    if not (missing_req or missing_pref):
        order.remove("learning quickly")
    behavioral = [Slot(Category.BEHAVIORAL, t, source="STAR") for t in order[:n_behavioral]]

    return project_slots + technical + behavioral


def _bullet_first(bullet: str, skills: list[str]) -> list[str]:
    """Order project skills so those named in the chosen bullet come first."""
    in_bullet = extract_skills(bullet)
    return in_bullet + [s for s in skills if s not in in_bullet]


# --------------------------------------------------------------------------- questions


class QuestionWriter:
    def __init__(self, llm: LLMClient, resume_context: str = "") -> None:
        self.llm = llm
        self.resume_context = resume_context

    def write(self, slot: Slot) -> Question:
        payload = slot.payload()
        request = LLMRequest(
            task="question",
            system=QUESTION_SYSTEM,
            user=question_user({**payload, "resume_summary": self.resume_context[:1200]}),
            payload=payload,
        )
        draft = structured_call(self.llm, request, QuestionDraft)
        return Question(
            category=slot.category, text=draft.text, topic=slot.topic,
            expected_points=draft.expected_points, source=slot.source,
        )

    def follow_up(self, question: Question, answer: str, score: RubricScore, kind: str) -> Question:
        _, missed = coverage(question, answer)
        weak = getattr(score, kind).feedback if kind != "stretch" else "Answer was strong."
        request = LLMRequest(
            task="followup",
            system=FOLLOWUP_SYSTEM,
            user=followup_user(question, answer, kind, weak),
            payload={"question": question.model_dump(mode="json"), "kind": kind,
                     "missed": [m.description for m in missed]},
        )
        draft = structured_call(self.llm, request, QuestionDraft)
        return Question(
            category=question.category, text=draft.text, topic=question.topic,
            expected_points=draft.expected_points, is_followup=True, followup_kind=kind,
            source=question.source,
        )


def choose_followup_kind(score: RubricScore) -> str | None:
    """Adaptive policy: probe the weakest dimension, or stretch a strong answer."""
    if score.overall >= STRETCH_AT:
        return "stretch"
    if score.overall < PROBE_BELOW:
        return score.weakest_dimension()
    return None


# --------------------------------------------------------------------------- session


@dataclass
class TurnResult:
    question: Question
    answer: str
    score: RubricScore
    followup: Question | None  # set when the agent decided to follow up


class InterviewSession:
    def __init__(
        self,
        llm: LLMClient,
        db: Database,
        session_id: int,
        plan: list[Slot],
        *,
        resume_context: str = "",
        max_followups: int = 1,
    ) -> None:
        self.db = db
        self.session_id = session_id
        self.writer = QuestionWriter(llm, resume_context)
        self.scorer = RubricScorer(llm)
        self.resume_context = resume_context
        self.max_followups = max_followups
        self._queue = list(plan)
        self._followups_used = 0
        self._turn_idx = 0
        self.total_main = len(plan)
        self.main_done = 0
        self.results: list[TurnResult] = []
        self.current: Question | None = self._next_main()

    @classmethod
    def start(
        cls,
        llm: LLMClient,
        db: Database,
        profile: ResumeProfile,
        jd: JobDescription,
        gap: GapReport,
        *,
        llm_label: str,
        n_technical: int = 3,
        n_project: int = 2,
        n_behavioral: int = 2,
        max_followups: int = 1,
    ) -> InterviewSession:
        plan = build_plan(profile, jd, gap, n_technical=n_technical, n_project=n_project,
                          n_behavioral=n_behavioral)
        profile_id = db.save_profile(profile)
        jd_id = db.save_job_description(jd)
        session_id = db.create_session(profile_id, jd_id, llm_label)
        context = _resume_context(profile)
        return cls(llm, db, session_id, plan, resume_context=context, max_followups=max_followups)

    @property
    def finished(self) -> bool:
        return self.current is None

    def _next_main(self) -> Question | None:
        if not self._queue:
            return None
        self._followups_used = 0
        return self.writer.write(self._queue.pop(0))

    def submit(
        self, answer: str, *, filler_count: int | None = None, wpm: float | None = None
    ) -> TurnResult:
        if self.current is None:
            raise RuntimeError("interview already finished")
        question = self.current
        score = self.scorer.score(question, answer, self.resume_context)
        self.db.add_turn(self.session_id, self._turn_idx, question, answer, score,
                         filler_count=filler_count, wpm=wpm)
        self._turn_idx += 1

        followup = None
        kind = choose_followup_kind(score)
        if kind and self._followups_used < self.max_followups and answer.strip():
            followup = self.writer.follow_up(question, answer, score, kind)
            self._followups_used += 1
        result = TurnResult(question, answer, score, followup)
        self.results.append(result)

        if followup is not None:
            self.current = followup
        else:
            self.main_done += 1  # this slot (main question + any follow-up) is complete
            self.current = self._next_main()
        if self.current is None:
            self.db.finish_session(self.session_id)
        return result

    def summary(self) -> dict[str, Any]:
        scores = [r.score for r in self.results]
        if not scores:
            return {"turns": 0, "overall": 0.0, "by_category": {}}
        by_cat: dict[str, list[float]] = {}
        for r in self.results:
            by_cat.setdefault(r.question.category.value, []).append(r.score.overall)
        return {
            "turns": len(scores),
            "overall": round(sum(s.overall for s in scores) / len(scores), 2),
            "by_category": {k: round(sum(v) / len(v), 2) for k, v in by_cat.items()},
        }


def _resume_context(profile: ResumeProfile) -> str:
    parts = [f"Skills: {', '.join(profile.skills)}"]
    for p in profile.projects:
        parts.append(f"Project {p.name}: " + " ".join(p.bullets))
    for e in profile.experience:
        parts.append(f"Experience {e.title}: " + " ".join(e.bullets))
    return "\n".join(parts)
