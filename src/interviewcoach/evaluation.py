"""Scorer evaluation: does the scorer rank good > mediocre > bad answers correctly?

The answer set is small and hand-written (see ``evals/``). Questions are produced by the same
deterministic question builder the app's mock mode uses, so the set is identical whichever
scorer (offline heuristic or a live LLM) is being tested. Results are reported honestly,
including a trivial word-count baseline, so the scorer has to beat "longer = better".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

from pydantic import BaseModel

from .llm.base import LLMRequest
from .llm.mock import MockLLM
from .llm.structured import structured_call
from .models import DIMENSIONS, Question, QuestionDraft
from .scoring import RubricScorer

TIERS = ("good", "mediocre", "bad")
LABEL = {"good": 3, "mediocre": 2, "bad": 1}


class EvalItem(BaseModel):
    id: str
    split: str
    slot: dict[str, Any]
    answers: dict[str, str]
    adversarial: dict[str, str] = {}


def build_question(slot: dict[str, Any]) -> Question:
    """Build a Question for a slot with the offline question writer (deterministic)."""
    payload = {"category": slot["category"], "topic": slot["topic"], "source": "eval",
               "context": slot.get("context", {}), "missing": slot.get("missing", False)}
    draft = structured_call(
        MockLLM(),
        LLMRequest(task="question", system="", user="", payload=payload),
        QuestionDraft,
    )
    return Question(category=slot["category"], text=draft.text, topic=slot["topic"],
                    expected_points=draft.expected_points)


def load_items(*paths: str | Path) -> list[EvalItem]:
    items: list[EvalItem] = []
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for raw in data["items"]:
            items.append(EvalItem(split=data["split"], **raw))
    return items


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    """Spearman rank correlation (average ranks for ties); 0.0 if either side is constant."""
    rx, ry = _ranks(x), _ranks(y)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 3) if den else 0.0


@dataclass
class Row:
    item_id: str
    split: str
    tier: str
    words: int
    overall: float
    dims: dict[str, int]


@dataclass
class Summary:
    n_items: int
    n_answers: int
    strict_order: int  # items with good > mediocre > bad
    pairwise_correct: int
    pairwise_total: int
    pairwise_ties: int
    spearman: float
    mean_overall: dict[str, float]
    mean_dims: dict[str, dict[str, float]]
    baseline_pairwise_correct: int  # word count as the "score"


@dataclass
class EvalReport:
    rows: list[Row] = field(default_factory=list)
    adversarial: list[tuple[str, str, float, int]] = field(default_factory=list)
    # (item id, kind, overall, rank among that item's 4 answers: 1 = highest)

    def subset(self, split: str | None) -> list[Row]:
        return [r for r in self.rows if split in (None, r.split)]

    def summarize(self, split: str | None = None) -> Summary:
        rows = self.subset(split)
        by_item: dict[str, dict[str, Row]] = {}
        for r in rows:
            by_item.setdefault(r.item_id, {})[r.tier] = r
        pairs = (("good", "mediocre"), ("mediocre", "bad"), ("good", "bad"))
        strict = pw_ok = pw_tot = ties = base_ok = 0
        for tiers in by_item.values():
            g, m, b = tiers["good"], tiers["mediocre"], tiers["bad"]
            strict += g.overall > m.overall > b.overall
            for hi, lo in pairs:
                a, c = tiers[hi], tiers[lo]
                pw_tot += 1
                pw_ok += a.overall > c.overall
                ties += a.overall == c.overall
                base_ok += a.words > c.words
        return Summary(
            n_items=len(by_item),
            n_answers=len(rows),
            strict_order=strict,
            pairwise_correct=pw_ok,
            pairwise_total=pw_tot,
            pairwise_ties=ties,
            spearman=spearman([r.overall for r in rows], [LABEL[r.tier] for r in rows]),
            mean_overall={t: round(mean(r.overall for r in rows if r.tier == t), 2)
                          for t in TIERS},
            mean_dims={t: {d: round(mean(r.dims[d] for r in rows if r.tier == t), 2)
                           for d in DIMENSIONS} for t in TIERS},
            baseline_pairwise_correct=base_ok,
        )


def run_eval(scorer: RubricScorer, items: list[EvalItem]) -> EvalReport:
    report = EvalReport()
    for item in items:
        question = build_question(item.slot)
        scored: dict[str, tuple[float, int, dict[str, int]]] = {}
        for tier, answer in item.answers.items():
            s = scorer.score(question, answer)
            row = Row(item.id, item.split, tier, len(answer.split()), s.overall,
                      s.dimension_scores())
            report.rows.append(row)
            scored[tier] = (s.overall, row.words, row.dims)
        for kind, answer in item.adversarial.items():
            s = scorer.score(question, answer)
            pool = sorted([v[0] for v in scored.values()] + [s.overall], reverse=True)
            report.adversarial.append((item.id, kind, s.overall, pool.index(s.overall) + 1))
    return report


# --------------------------------------------------------------------------- rendering


def render_markdown(report: EvalReport, scorer_label: str) -> str:
    lines = [f"**Scorer under test:** {scorer_label}", ""]
    lines += ["| Split | Questions | Answers | Strict order (good > mediocre > bad) | "
              "Pairwise correct | Ties | Spearman ρ vs. label | Word-count baseline pairwise |",
              "|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|"]
    for split, name in (("dev", "dev"), ("heldout", "held-out"), (None, "**all**")):
        if not report.subset(split):
            continue
        s = report.summarize(split)
        lines.append(
            f"| {name} | {s.n_items} | {s.n_answers} | {s.strict_order}/{s.n_items} | "
            f"{s.pairwise_correct}/{s.pairwise_total} | {s.pairwise_ties} | {s.spearman:+.2f} | "
            f"{s.baseline_pairwise_correct}/{s.pairwise_total} |"
        )
    s = report.summarize()
    lines += ["", "| Tier | Mean overall (1-5) | " + " | ".join(DIMENSIONS) + " |",
              "|---|:-:|" + ":-:|" * len(DIMENSIONS)]
    for t in TIERS:
        lines.append(f"| {t} | {s.mean_overall[t]:.2f} | "
                     + " | ".join(f"{s.mean_dims[t][d]:.2f}" for d in DIMENSIONS) + " |")
    if report.adversarial:
        lines += ["", "| Adversarial (keyword-stuffed, no real explanation) | Overall | "
                      "Rank among that item's 4 answers (1 = best) |", "|---|:-:|:-:|"]
        for item_id, kind, overall, rank in report.adversarial:
            lines.append(f"| {item_id} / {kind} | {overall:.2f} | {rank} |")
    return "\n".join(lines)


def per_answer_table(report: EvalReport) -> str:
    lines = ["| Item | Split | Tier | Words | Overall |", "|---|---|---|:-:|:-:|"]
    for r in report.rows:
        lines.append(f"| {r.item_id} | {r.split} | {r.tier} | {r.words} | {r.overall:.2f} |")
    return "\n".join(lines)
