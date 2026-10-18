from __future__ import annotations

import pandas as pd

from interviewcoach.models import Category, ExpectedPoint, Question
from interviewcoach.progress import (
    category_trend,
    dimension_averages,
    session_trend,
    speech_summary,
    turns_frame,
    weakest_topics,
)
from interviewcoach.scoring import RubricScorer


def add(db, sid, idx, topic, category, answer, **kw):
    q = Question(category=category, text="Explain how chunking works in retrieval.", topic=topic,
                 expected_points=[ExpectedPoint(description="chunking", keywords=["chunk"])])
    from interviewcoach.llm import MockLLM

    db.add_turn(sid, idx, q, answer, RubricScorer(MockLLM()).score(q, answer), **kw)


STRONG = ("First, I split documents into chunks because whole files are too large. For example "
          "chunks of 300 tokens. Then I embed each chunk. The trade-off is overlap versus index "
          "size, since more overlap costs storage.")


def test_empty_database_gives_empty_results(db):
    df = turns_frame(db)
    assert df.empty and category_trend(df).empty and weakest_topics(df) == []
    assert speech_summary(df) is None and session_trend(df).empty
    assert dimension_averages(df).empty


def test_trend_and_weakest_topics(db):
    s1, s2 = db.create_session(None, None, "mock"), db.create_session(None, None, "mock")
    add(db, s1, 0, "RAG", Category.TECHNICAL, "idk")
    add(db, s1, 1, "Conflict", Category.BEHAVIORAL, "idk")
    add(db, s2, 0, "RAG", Category.TECHNICAL, STRONG)
    add(db, s2, 1, "Conflict", Category.BEHAVIORAL, "idk")
    df = turns_frame(db)
    trend = category_trend(df)
    assert list(trend.index) == [s1, s2]
    assert trend.loc[s2, "technical"] > trend.loc[s1, "technical"]
    assert session_trend(df)[s2] > session_trend(df)[s1]
    weakest = weakest_topics(df, limit=2)
    assert weakest[0].topic == "Conflict" and weakest[0].avg_score < weakest[1].avg_score
    assert weakest[0].weakest_dimension in ("correctness", "depth", "clarity", "structure",
                                            "relevance")
    assert weakest[0].advice
    dims = dimension_averages(df)
    assert dims.is_monotonic_increasing


def test_speech_summary_ignores_typed_answers(db):
    sid = db.create_session(None, None, "mock")
    add(db, sid, 0, "RAG", Category.TECHNICAL, STRONG)  # typed: no wpm
    add(db, sid, 1, "RAG", Category.TECHNICAL, STRONG, filler_count=4, wpm=150.0)
    add(db, sid, 2, "RAG", Category.TECHNICAL, STRONG, filler_count=2, wpm=130.0)
    summary = speech_summary(turns_frame(db))
    assert summary == {"answers": 2.0, "avg_wpm": 140.0, "avg_fillers": 3.0}
    assert isinstance(turns_frame(db)["created_at"].iloc[0], pd.Timestamp)
