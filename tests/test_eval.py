from __future__ import annotations

from pathlib import Path

import pytest

from interviewcoach.evaluation import (
    build_question,
    load_items,
    render_markdown,
    run_eval,
    spearman,
)
from interviewcoach.llm import MockLLM
from interviewcoach.scoring import RubricScorer

EVALS = Path(__file__).resolve().parents[1] / "evals"


def test_spearman_known_values():
    assert spearman([1, 2, 3], [1, 2, 3]) == 1.0
    assert spearman([1, 2, 3], [3, 2, 1]) == -1.0
    assert spearman([1, 1, 1], [1, 2, 3]) == 0.0  # constant side has no rank correlation
    assert spearman([1, 2, 2, 3], [1, 2, 3, 4]) == pytest.approx(0.949, abs=0.001)


def test_eval_set_is_well_formed():
    items = load_items(EVALS / "answers_dev.json", EVALS / "answers_heldout.json")
    assert {i.split for i in items} == {"dev", "heldout"}
    assert len({i.id for i in items}) == len(items)
    for item in items:
        assert set(item.answers) == {"good", "mediocre", "bad"}
        assert build_question(item.slot).expected_points


@pytest.fixture(scope="module")
def report():
    items = load_items(EVALS / "answers_dev.json", EVALS / "answers_heldout.json")
    return run_eval(RubricScorer(MockLLM()), items)


def test_offline_scorer_regression_matches_readme_numbers(report):
    """If this fails, the README's evaluation table is out of date: re-run `interviewcoach eval`."""
    dev, held, both = report.summarize("dev"), report.summarize("heldout"), report.summarize()
    assert (dev.strict_order, dev.n_items, dev.pairwise_correct, dev.pairwise_total) == (6, 6, 18, 18)
    assert (held.strict_order, held.n_items, held.pairwise_correct) == (3, 4, 11)
    assert both.pairwise_correct == 29 and both.pairwise_total == 30
    assert both.mean_overall["good"] > both.mean_overall["mediocre"] > both.mean_overall["bad"]


def test_scorer_beats_word_count_baseline(report):
    both = report.summarize()
    assert both.pairwise_correct > both.baseline_pairwise_correct


def test_markdown_report_mentions_scorer_and_adversarial_rows(report):
    md = render_markdown(report, "heuristic")
    assert "heuristic" in md and "Adversarial" in md and "held-out" in md
