from __future__ import annotations

import pytest

from interviewcoach.interview import (
    InterviewSession,
    build_plan,
    choose_followup_kind,
)
from interviewcoach.models import Category
from interviewcoach.scoring import RubricScorer

GOOD_PROJECT = (
    "The core design is a library of attacks defined in YAML, each paired with a detector, so "
    "adding an attack doesn't need new code. I chose that because I wanted the 48 attacks to be "
    "easy to review and extend. The hardest problem was detecting leaks reliably: a plain string "
    "match missed a secret that came back reversed or base64-encoded, so I planted a canary "
    "token in the system prompt and normalised responses before checking. I verified it by "
    "running the tool against a deliberately vulnerable demo bot and a hardened one and "
    "checking the scores differed, plus unit tests for each detector. Next I'd add more "
    "indirect-injection cases."
)


def test_plan_has_requested_mix_and_order(profile, jd, gap):
    plan = build_plan(profile, jd, gap, n_technical=3, n_project=2, n_behavioral=2)
    cats = [s.category for s in plan]
    assert cats == [Category.PROJECT] * 2 + [Category.TECHNICAL] * 3 + [Category.BEHAVIORAL] * 2


def test_project_questions_come_from_resume_projects(profile, jd, gap):
    plan = build_plan(profile, jd, gap, n_project=3)
    projects = [s for s in plan if s.category == Category.PROJECT]
    names = {p.name for p in profile.projects}
    assert {s.topic for s in projects} <= names
    assert all(s.context["bullet"] for s in projects)


def test_technical_plan_probes_a_missing_skill_and_prefers_jd_priorities(profile, jd, gap):
    tech = [s for s in build_plan(profile, jd, gap) if s.category == Category.TECHNICAL]
    missing = [s for s in tech if s.missing]
    assert [s.topic for s in missing] == ["AWS"]  # the only missing required/preferred skill
    assert all(s.topic in jd.required_skills + jd.preferred_skills for s in tech)


def test_plan_respects_zero_counts(profile, jd, gap):
    plan = build_plan(profile, jd, gap, n_technical=0, n_project=0, n_behavioral=1)
    assert [s.category for s in plan] == [Category.BEHAVIORAL]


def test_followup_policy_thresholds(llm, profile, jd, gap):
    scorer = RubricScorer(llm)
    session = InterviewSession.start(llm, _fresh_db(), profile, jd, gap, llm_label="mock")
    q = session.current
    strong = scorer.score(q, GOOD_PROJECT)
    weak = scorer.score(q, "idk")
    assert choose_followup_kind(weak) == weak.weakest_dimension()
    assert strong.overall >= 4.0
    assert choose_followup_kind(strong) in (None, "stretch")


def _fresh_db():
    from interviewcoach.db import Database

    return Database(":memory:")


def test_full_session_persists_every_turn_and_finishes(llm, profile, jd, gap):
    db = _fresh_db()
    session = InterviewSession.start(llm, db, profile, jd, gap, llm_label="mock",
                                     n_technical=1, n_project=1, n_behavioral=1)
    guard = 0
    while not session.finished:
        session.submit("I think it is basically stuff.")
        guard += 1
        assert guard < 20
    rows = db.turns(session.session_id)
    assert len(rows) == len(session.results) >= 3
    assert [r["idx"] for r in rows] == list(range(len(rows)))
    assert db.sessions()[0]["ended_at"] is not None
    assert session.main_done == session.total_main == 3
    with pytest.raises(RuntimeError):
        session.submit("more")


def test_weak_answer_triggers_adaptive_followup_on_weakest_dimension(llm, profile, jd, gap):
    session = InterviewSession.start(llm, _fresh_db(), profile, jd, gap, llm_label="mock")
    first = session.current
    result = session.submit("not sure")
    assert result.followup is not None and session.current is result.followup
    assert result.followup.is_followup
    assert result.followup.followup_kind == result.score.weakest_dimension()
    assert result.followup.topic == first.topic


def test_strong_answer_gets_stretch_followup_and_only_one_followup(llm, profile, jd, gap):
    session = InterviewSession.start(llm, _fresh_db(), profile, jd, gap, llm_label="mock",
                                     max_followups=1)
    first = session.submit(GOOD_PROJECT)
    assert first.followup is not None and first.followup.followup_kind == "stretch"
    second = session.submit("idk")  # would normally trigger another follow-up
    assert second.followup is None  # capped at one per question
    assert session.current is not None and not session.current.is_followup


def test_followups_can_be_disabled(llm, profile, jd, gap):
    session = InterviewSession.start(llm, _fresh_db(), profile, jd, gap, llm_label="mock",
                                     max_followups=0)
    assert session.submit("not sure").followup is None


def test_skipped_answer_does_not_trigger_followup(llm, profile, jd, gap):
    session = InterviewSession.start(llm, _fresh_db(), profile, jd, gap, llm_label="mock")
    result = session.submit("")
    assert result.score.overall == 1.0 and result.followup is None


def test_summary_averages_by_category(llm, profile, jd, gap):
    session = InterviewSession.start(llm, _fresh_db(), profile, jd, gap, llm_label="mock",
                                     max_followups=0)
    session.submit(GOOD_PROJECT)
    summary = session.summary()
    assert summary["turns"] == 1 and "project" in summary["by_category"]
