from __future__ import annotations

import sqlite3

import pytest

from interviewcoach.llm import MockLLM
from interviewcoach.models import Category, ExpectedPoint, Question
from interviewcoach.scoring import RubricScorer


def make_turn(db, session_id, idx, topic="RAG", category=Category.TECHNICAL, answer="chunk it"):
    q = Question(category=category, text="Explain retrieval augmented generation.", topic=topic,
                 expected_points=[ExpectedPoint(description="chunking", keywords=["chunk"])])
    score = RubricScorer(MockLLM()).score(q, answer)
    db.add_turn(session_id, idx, q, answer, score, filler_count=2, wpm=130.5)
    return score


def test_roundtrip_session_and_turns(db, profile, jd):
    pid, jid = db.save_profile(profile), db.save_job_description(jd)
    sid = db.create_session(pid, jid, "mock")
    score = make_turn(db, sid, 0)
    db.finish_session(sid)
    rows = db.turns(sid)
    assert len(rows) == 1
    row = rows[0]
    assert row["overall"] == score.overall and row["topic"] == "RAG"
    assert row["filler_count"] == 2 and row["wpm"] == 130.5
    (session,) = db.sessions()
    assert session["n_turns"] == 1 and session["ended_at"] is not None
    assert session["avg_overall"] == pytest.approx(score.overall, abs=0.01)


def test_raw_resume_text_is_not_stored(db, profile):
    assert profile.raw_text  # parsed profile has it in memory...
    db.save_profile(profile)
    stored = db.turns() or db._all("SELECT profile_json FROM profiles")
    assert "raw_text" not in stored[0]["profile_json"]
    assert "Campus Notes" in stored[0]["profile_json"]  # ...but the parsed structure is kept


def test_check_constraint_rejects_out_of_range_scores(db):
    sid = db.create_session(None, None, "mock")
    with pytest.raises(sqlite3.IntegrityError):
        with db._tx() as cur:
            cur.execute(
                "INSERT INTO turns(session_id, idx, category, topic, question, answer, "
                "correctness, depth, clarity, structure, relevance, overall, score_json, "
                "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, 0, "technical", "x", "q", "a", 9, 1, 1, 1, 1, 2.6, "{}", "now"))


def test_foreign_key_requires_existing_session(db):
    with pytest.raises(sqlite3.IntegrityError):
        make_turn(db, 999, 0)


def test_delete_all_erases_everything_and_resets_ids(db, profile, jd):
    sid = db.create_session(db.save_profile(profile), db.save_job_description(jd), "mock")
    make_turn(db, sid, 0)
    assert all(v == 1 for v in db.counts().values())
    db.delete_all()
    assert db.counts() == {"profiles": 0, "job_descriptions": 0, "sessions": 0, "turns": 0}
    assert db.create_session(None, None, "mock") == 1  # autoincrement reset


def test_delete_all_removes_content_from_file(tmp_path, profile):
    path = tmp_path / "ic.db"
    from interviewcoach.db import Database

    database = Database(path)
    database.save_profile(profile)
    database.delete_all()
    database.close()
    assert b"Campus Notes" not in path.read_bytes()


def test_database_creates_parent_directory(tmp_path):
    from interviewcoach.db import Database

    database = Database(tmp_path / "nested" / "dir" / "x.db")
    assert (tmp_path / "nested" / "dir" / "x.db").exists()
    database.close()
