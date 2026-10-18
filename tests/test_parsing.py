from __future__ import annotations

import pytest

from interviewcoach.parsing import (
    ParseError,
    extract_text,
    parse_job_description,
    parse_resume,
    split_sections,
)
from interviewcoach.skills import extract_skills


@pytest.mark.parametrize("filename", ["resume.pdf", "resume.docx", "resume.txt"])
def test_sample_resume_parses_identically_across_formats(sample_dir, filename):
    profile = parse_resume(extract_text((sample_dir / filename).read_bytes(), filename))
    assert profile.name == "Aryaveer Mankotia"
    assert profile.email == "aryaveer@example.com"
    assert "github.com/Aryaveer009" in profile.links
    assert [p.name for p in profile.projects] == ["PromptShield", "ModelRouter",
                                                  "Campus Notes Q&A"]
    assert [len(p.bullets) for p in profile.projects] == [4, 3, 2]
    assert len(profile.experience) == 1 and len(profile.experience[0].bullets) == 2
    assert {"Python", "SQL", "LLMs", "RAG", "OWASP"} <= set(profile.skills)


def test_project_skills_are_extracted_per_project(profile):
    by_name = {p.name: set(p.skills) for p in profile.projects}
    assert {"FastAPI", "Docker", "REST APIs"} <= by_name["ModelRouter"]
    assert {"RAG", "SQLite"} <= by_name["Campus Notes Q&A"]
    assert "Docker" not in by_name["PromptShield"]


def test_skills_listed_vs_found_anywhere(profile):
    assert "Threat Modeling" in profile.skills_listed
    assert "Docker" in profile.skills_listed and "Docker" in profile.skills


def test_split_sections_detects_headings_and_ignores_bullets():
    text = "Jane\nPROJECTS\n- Skills: not a heading\nSKILLS:\nPython"
    sections = split_sections(text)
    assert sections["projects"] == ["- Skills: not a heading"]
    assert sections["skills"] == ["Python"]


def test_wrapped_bullets_are_joined():
    text = ("Jane\nProjects\nTool | Python\n- Built a thing that does something quite\n"
            "long and wraps onto the next line.\n- Second bullet.\n")
    project = parse_resume(text).projects[0]
    assert len(project.bullets) == 2
    assert project.bullets[0].endswith("wraps onto the next line.")


def test_extract_text_rejects_unsupported_and_empty():
    with pytest.raises(ParseError, match="Unsupported"):
        extract_text(b"x", "resume.exe")
    with pytest.raises(ParseError, match="No text"):
        extract_text(b"   \n ", "resume.txt")
    with pytest.raises(ParseError, match="Could not read"):
        extract_text(b"not a pdf", "resume.pdf")


@pytest.mark.parametrize(
    ("text", "expected", "absent"),
    [
        ("I know JavaScript and Java", {"JavaScript", "Java"}, set()),
        ("Only javascript here", {"JavaScript"}, {"Java"}),
        ("C++ and C# developer", {"C++", "C#"}, {"Go"}),
        ("built with Node.js and Postgres", {"Node.js", "PostgreSQL"}, set()),
        ("retrieval-augmented generation pipelines", {"RAG"}, set()),
    ],
)
def test_skill_extraction_respects_word_boundaries(text, expected, absent):
    found = set(extract_skills(text))
    assert expected <= found
    assert not (absent & found)


def test_job_description_required_vs_preferred(jd):
    assert jd.title == "Junior AI Security Engineer"
    assert {"Python", "SQL", "LLMs", "RAG", "Docker", "Kubernetes", "OWASP"} <= set(
        jd.required_skills)
    assert set(jd.preferred_skills) == {"PostgreSQL", "AWS", "Terraform", "Penetration Testing"}
    assert not set(jd.required_skills) & set(jd.preferred_skills)
    assert any("security tests" in r for r in jd.responsibilities)


def test_job_description_without_headings_treats_skills_as_required():
    jd = parse_job_description("Backend Engineer\nWe use Python and Redis daily.")
    assert set(jd.required_skills) == {"Python", "Redis"}
    assert jd.preferred_skills == []
