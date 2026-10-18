from __future__ import annotations

from pathlib import Path

import pytest

from interviewcoach.db import Database
from interviewcoach.gap import analyze_gap
from interviewcoach.llm import MockLLM
from interviewcoach.parsing import extract_text, parse_job_description, parse_resume

SAMPLE = Path(__file__).resolve().parents[1] / "src" / "interviewcoach" / "sample_data"


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    return SAMPLE


@pytest.fixture(scope="session")
def profile():
    return parse_resume(extract_text((SAMPLE / "resume.pdf").read_bytes(), "resume.pdf"))


@pytest.fixture(scope="session")
def jd():
    return parse_job_description((SAMPLE / "job_description.txt").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def gap(profile, jd):
    return analyze_gap(profile, jd)


@pytest.fixture()
def db() -> Database:
    database = Database(":memory:")
    yield database
    database.close()


@pytest.fixture()
def llm() -> MockLLM:
    return MockLLM()
