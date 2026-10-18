"""SQLite persistence. Everything the app remembers lives in this one local file."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import DIMENSIONS, JobDescription, Question, ResumeProfile, RubricScore

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TEXT NOT NULL,
    name         TEXT,
    profile_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job_descriptions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    title      TEXT,
    jd_json    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE SET NULL,
    jd_id      INTEGER REFERENCES job_descriptions(id) ON DELETE SET NULL,
    started_at TEXT NOT NULL,
    ended_at   TEXT,
    llm_label  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS turns (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    idx           INTEGER NOT NULL,
    category      TEXT NOT NULL,
    topic         TEXT NOT NULL,
    is_followup   INTEGER NOT NULL DEFAULT 0,
    question      TEXT NOT NULL,
    answer        TEXT NOT NULL,
    correctness   INTEGER NOT NULL CHECK (correctness BETWEEN 1 AND 5),
    depth         INTEGER NOT NULL CHECK (depth BETWEEN 1 AND 5),
    clarity       INTEGER NOT NULL CHECK (clarity BETWEEN 1 AND 5),
    structure     INTEGER NOT NULL CHECK (structure BETWEEN 1 AND 5),
    relevance     INTEGER NOT NULL CHECK (relevance BETWEEN 1 AND 5),
    overall       REAL NOT NULL,
    score_json    TEXT NOT NULL,
    filler_count  INTEGER,
    wpm           REAL,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Database:
    """Thin wrapper around one SQLite connection (thread-safe via a lock)."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._tx() as cur:
            cur.execute("PRAGMA foreign_keys = ON")
            cur.execute("PRAGMA secure_delete = ON")  # zero out deleted content
            cur.executescript(SCHEMA)

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------ writes

    def save_profile(self, profile: ResumeProfile) -> int:
        # The raw resume text is deliberately not stored, only the parsed structure.
        payload = profile.model_dump_json(exclude={"raw_text"})
        with self._tx() as cur:
            cur.execute(
                "INSERT INTO profiles(created_at, name, profile_json) VALUES (?,?,?)",
                (_now(), profile.name, payload),
            )
            return int(cur.lastrowid or 0)

    def save_job_description(self, jd: JobDescription) -> int:
        with self._tx() as cur:
            cur.execute(
                "INSERT INTO job_descriptions(created_at, title, jd_json) VALUES (?,?,?)",
                (_now(), jd.title, jd.model_dump_json()),
            )
            return int(cur.lastrowid or 0)

    def create_session(self, profile_id: int | None, jd_id: int | None, llm_label: str) -> int:
        with self._tx() as cur:
            cur.execute(
                "INSERT INTO sessions(profile_id, jd_id, started_at, llm_label) VALUES (?,?,?,?)",
                (profile_id, jd_id, _now(), llm_label),
            )
            return int(cur.lastrowid or 0)

    def finish_session(self, session_id: int) -> None:
        with self._tx() as cur:
            cur.execute("UPDATE sessions SET ended_at=? WHERE id=?", (_now(), session_id))

    def add_turn(
        self,
        session_id: int,
        idx: int,
        question: Question,
        answer: str,
        score: RubricScore,
        *,
        filler_count: int | None = None,
        wpm: float | None = None,
    ) -> int:
        dims = score.dimension_scores()
        with self._tx() as cur:
            cur.execute(
                """INSERT INTO turns(session_id, idx, category, topic, is_followup, question,
                   answer, correctness, depth, clarity, structure, relevance, overall,
                   score_json, filler_count, wpm, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    session_id, idx, question.category.value, question.topic,
                    int(question.is_followup), question.text, answer,
                    *(dims[d] for d in DIMENSIONS), score.overall, score.model_dump_json(),
                    filler_count, wpm, _now(),
                ),
            )
            return int(cur.lastrowid or 0)

    # ------------------------------------------------------------------ reads

    def _all(self, sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._tx() as cur:
            return [dict(r) for r in cur.execute(sql, args).fetchall()]

    def sessions(self) -> list[dict[str, Any]]:
        return self._all(
            """SELECT s.id, s.started_at, s.ended_at, s.llm_label,
                      COUNT(t.id) AS n_turns, ROUND(AVG(t.overall), 2) AS avg_overall
               FROM sessions s LEFT JOIN turns t ON t.session_id = s.id
               GROUP BY s.id ORDER BY s.id"""
        )

    def turns(self, session_id: int | None = None) -> list[dict[str, Any]]:
        if session_id is None:
            return self._all("SELECT * FROM turns ORDER BY session_id, idx")
        return self._all("SELECT * FROM turns WHERE session_id=? ORDER BY idx", (session_id,))

    def counts(self) -> dict[str, int]:
        with self._tx() as cur:
            return {
                t: int(cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                for t in ("profiles", "job_descriptions", "sessions", "turns")
            }

    # ------------------------------------------------------------------ privacy

    def delete_all(self) -> None:
        """Erase every row (the "delete my data" button) and compact the file."""
        with self._tx() as cur:
            for table in ("turns", "sessions", "job_descriptions", "profiles"):
                cur.execute(f"DELETE FROM {table}")
            cur.execute("DELETE FROM sqlite_sequence")
        with self._lock:
            self._conn.execute("VACUUM")
