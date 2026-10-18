from __future__ import annotations

from interviewcoach.gap import analyze_gap
from interviewcoach.models import GapStatus, JobDescription, ResumeProfile
from interviewcoach.parsing import parse_job_description, parse_resume


def _status(gap, skill):
    return next(i for i in gap.items if i.skill == skill)


def test_sample_gap_statuses(gap):
    assert _status(gap, "Python").status == GapStatus.COVERED
    assert "PromptShield" in (_status(gap, "Python").evidence or "")
    assert _status(gap, "SQL").status == GapStatus.COVERED  # implied by SQLite in a project
    # listed in Skills but no project shows it -> partial
    assert _status(gap, "Threat Modeling").status == GapStatus.PARTIAL
    # Docker on the resume, Kubernetes wanted: same family -> partial
    k8s = _status(gap, "Kubernetes")
    assert k8s.status == GapStatus.PARTIAL and "Docker" in (k8s.evidence or "")
    assert _status(gap, "AWS").status == GapStatus.MISSING
    assert _status(gap, "AWS").importance == "preferred"


def test_coverage_percentage_is_weighted_and_bounded(gap):
    assert 0 < gap.coverage_pct < 100
    assert len(gap.by_status(GapStatus.COVERED)) + len(gap.by_status(GapStatus.PARTIAL)) + len(
        gap.by_status(GapStatus.MISSING)) == len(gap.items)


def test_empty_jd_gives_zero_items():
    report = analyze_gap(ResumeProfile(), JobDescription())
    assert report.items == [] and report.coverage_pct == 0.0


def test_required_miss_costs_more_than_preferred_miss():
    resume = parse_resume("Jo\nSkills\nPython\nProjects\nTool\n- Built in Python.\n")
    miss_required = analyze_gap(resume, parse_job_description("Role\nRequirements\n- Python\n- Rust"))
    miss_preferred = analyze_gap(
        resume, parse_job_description("Role\nRequirements\n- Python\nNice to have\n- Rust"))
    assert miss_required.coverage_pct < miss_preferred.coverage_pct
