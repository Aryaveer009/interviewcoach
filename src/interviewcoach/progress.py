"""Progress dashboard maths: trends per category, weakest areas, suggested practice."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .db import Database
from .models import DIMENSIONS

PRACTICE_TIPS = {
    "correctness": "review the fundamentals and write a 3-bullet cheat sheet",
    "depth": "practise adding a concrete example and one trade-off to every answer",
    "clarity": "drill 30-second answers; cut hedges like 'I think' and 'kind of'",
    "structure": "use a fixed frame: summary, reasoning, example (STAR for behavioural)",
    "relevance": "restate the question first, then answer it before adding detail",
}


@dataclass
class Suggestion:
    topic: str
    category: str
    avg_score: float
    weakest_dimension: str
    advice: str


def turns_frame(db: Database) -> pd.DataFrame:
    rows = db.turns()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def category_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Average overall score per session (rows) and category (columns)."""
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby(["session_id", "category"])["overall"].mean().round(2).unstack("category")
    )


def session_trend(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    return df.groupby("session_id")["overall"].mean().round(2)


def dimension_averages(df: pd.DataFrame) -> pd.Series:
    """Mean score per rubric dimension, lowest first."""
    if df.empty:
        return pd.Series(dtype=float)
    return df[list(DIMENSIONS)].mean().round(2).sort_values()


def weakest_topics(df: pd.DataFrame, limit: int = 3) -> list[Suggestion]:
    """Topics with the lowest average score, each with the dimension to work on."""
    if df.empty:
        return []
    out: list[Suggestion] = []
    ranked = (
        df.groupby(["topic", "category"])["overall"].mean().reset_index().sort_values("overall")
    )
    top = ranked.head(limit)
    for topic, category, avg in zip(top["topic"], top["category"], top["overall"], strict=True):
        sub = df[(df["topic"] == topic) & (df["category"] == category)]
        dim = str(sub[list(DIMENSIONS)].mean().idxmin())
        out.append(Suggestion(str(topic), str(category), round(float(avg), 2), dim,
                              PRACTICE_TIPS[dim]))
    return out


def speech_summary(df: pd.DataFrame) -> dict[str, float] | None:
    """Average fillers and pace over spoken answers, or None if there are none."""
    if df.empty or df["wpm"].isna().all():
        return None
    spoken = df.dropna(subset=["wpm"])
    return {
        "answers": float(len(spoken)),
        "avg_wpm": round(float(spoken["wpm"].mean()), 1),
        "avg_fillers": round(float(spoken["filler_count"].mean()), 2),
    }
