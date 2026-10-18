"""Skills-gap analysis: which JD requirements does the resume cover?

Rules (documented in the README so they can be explained and challenged):

* **covered**  - the skill (or something that implies it, e.g. PostgreSQL -> SQL) appears
  in a project or experience entry, i.e. there is evidence of *using* it.
* **partial**  - it is only listed in the Skills section with no project/experience
  evidence, OR the resume has a *related* skill from the same family (e.g. the JD wants
  PostgreSQL, the resume has MySQL).
* **missing**  - neither of the above.
"""

from __future__ import annotations

from .models import GapReport, GapStatus, JobDescription, ResumeProfile, SkillGapItem
from .skills import expand_implied, family_of


def _evidence_sources(profile: ResumeProfile) -> list[tuple[str, set[str]]]:
    sources = [(f"project “{p.name}”", expand_implied(set(p.skills))) for p in profile.projects]
    sources += [(f"experience “{e.title.split('|')[0].strip()}”", expand_implied(set(e.skills)))
                for e in profile.experience]
    return sources


def analyze_gap(profile: ResumeProfile, jd: JobDescription) -> GapReport:
    sources = _evidence_sources(profile)
    listed = expand_implied(set(profile.skills_listed))
    anywhere = expand_implied(set(profile.skills))
    items: list[SkillGapItem] = []

    wanted = [(s, "required") for s in jd.required_skills] + [
        (s, "preferred") for s in jd.preferred_skills
    ]
    for skill, importance in wanted:
        evidence = next((label for label, skills in sources if skill in skills), None)
        if evidence:
            status, note = GapStatus.COVERED, f"Used in {evidence}"
        elif skill in listed or skill in anywhere:
            status, note = GapStatus.PARTIAL, "Listed on the resume but no project/experience shows it"
        else:
            family = family_of(skill)
            related = sorted(
                s for s in anywhere if s != skill and family and family_of(s) == family
            )
            if related:
                status, note = GapStatus.PARTIAL, f"Related skill on resume: {', '.join(related[:3])}"
            else:
                status, note = GapStatus.MISSING, None
        items.append(SkillGapItem(skill=skill, importance=importance, status=status, evidence=note))
    return GapReport(items=items)
