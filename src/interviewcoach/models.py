"""Pydantic data models shared across the whole app.

Everything the LLM returns is validated against these models, so a malformed
model response is caught (and retried) instead of leaking into the UI or DB.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    TECHNICAL = "technical"
    PROJECT = "project"
    BEHAVIORAL = "behavioral"


class GapStatus(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    MISSING = "missing"


# --------------------------------------------------------------------------- resume / JD


class Project(BaseModel):
    name: str
    description: str = ""
    bullets: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join([self.name, self.description, *self.bullets])


class Experience(BaseModel):
    title: str
    bullets: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join([self.title, *self.bullets])


class ResumeProfile(BaseModel):
    name: str | None = None
    email: str | None = None
    links: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list, description="All skills found anywhere")
    skills_listed: list[str] = Field(
        default_factory=list, description="Skills found in the Skills section"
    )
    projects: list[Project] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    raw_text: str = ""


class JobDescription(BaseModel):
    title: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    raw_text: str = ""


class SkillGapItem(BaseModel):
    skill: str
    importance: str  # "required" | "preferred"
    status: GapStatus
    evidence: str | None = None


class GapReport(BaseModel):
    items: list[SkillGapItem] = Field(default_factory=list)

    def by_status(self, status: GapStatus) -> list[SkillGapItem]:
        return [i for i in self.items if i.status == status]

    @property
    def coverage_pct(self) -> float:
        """Weighted coverage: required skills count 2x, partial counts half."""
        total = got = 0.0
        for item in self.items:
            weight = 2.0 if item.importance == "required" else 1.0
            total += weight
            got += weight * {"covered": 1.0, "partial": 0.5, "missing": 0.0}[item.status.value]
        return round(100 * got / total, 1) if total else 0.0


# --------------------------------------------------------------------------- questions


class ExpectedPoint(BaseModel):
    description: str
    keywords: list[str] = Field(default_factory=list)


class Question(BaseModel):
    category: Category
    text: str = Field(min_length=10)
    topic: str
    expected_points: list[ExpectedPoint] = Field(default_factory=list)
    is_followup: bool = False
    followup_kind: str | None = None
    source: str = ""  # project name / JD skill the question was drawn from


class QuestionDraft(BaseModel):
    """What the LLM must return when asked to write one question."""

    text: str = Field(min_length=10)
    expected_points: list[ExpectedPoint] = Field(min_length=1)


# --------------------------------------------------------------------------- scoring

DIMENSIONS = ("correctness", "depth", "clarity", "structure", "relevance")


class DimensionScore(BaseModel):
    score: int = Field(ge=1, le=5)
    feedback: str = Field(min_length=3)

    @field_validator("feedback")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class RubricScore(BaseModel):
    correctness: DimensionScore
    depth: DimensionScore
    clarity: DimensionScore
    structure: DimensionScore
    relevance: DimensionScore
    overall_feedback: str = Field(min_length=3)
    sample_answer: str = Field(min_length=20)

    @property
    def overall(self) -> float:
        return round(sum(self.dimension_scores().values()) / len(DIMENSIONS), 2)

    def dimension_scores(self) -> dict[str, int]:
        return {d: getattr(self, d).score for d in DIMENSIONS}

    def weakest_dimension(self) -> str:
        scores = self.dimension_scores()
        # Stable tie-break: first in rubric order.
        return min(DIMENSIONS, key=lambda d: scores[d])
