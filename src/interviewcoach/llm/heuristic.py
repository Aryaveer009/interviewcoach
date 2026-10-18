"""Offline rubric scorer used by mock mode.

This is a *lexical heuristic*, not an LLM judgement. It checks how many of the question's
expected points the answer touches (keyword coverage), and measures surface features of the
answer: length, concrete specifics, reasoning connectors, sequencing words, hedging/filler
density. It exists so the app and test-suite run with no API key, and so there is an
inspectable baseline to compare an LLM judge against. Its known weaknesses (it rewards
vocabulary, can be gamed, cannot verify facts) are reported in the README.
"""

from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache

from ..knowledge import STAR_POINTS
from ..models import Category, DimensionScore, ExpectedPoint, Question, RubricScore
from ..skills import extract_skills

_WORD = re.compile(r"[a-z0-9][a-z0-9'+#./-]*")
_STOP = frozenset(
    "the a an and or of to in on for with is are was were be been it its this that these those "
    "you your i me my we our how what why when where which would could should can do does did "
    "about from into than then them they their there have has had not but if as at by so such "
    "tell describe explain walk through me".split()
)

HEDGES = ("i think", "maybe", "probably", "i guess", "not sure", "i'm not sure", "kind of",
          "sort of", "something like", "i don't know", "dunno", "no idea", "i suppose")
FILLERS = ("um", "uh", "erm", "hmm", "you know", "basically", "literally", "i mean")
VAGUE = ("stuff", "things", "thing", "something", "somehow", "whatever", "etc", "and so on")
CONNECTORS = ("because", "since", "so that", "therefore", "instead of", "trade-off", "tradeoff",
              "however", "whereas", "which means", "as a result", "rather than", "in order to",
              "due to", "compared to", "versus", "otherwise", "which is why", "this means")
SEQUENCE = ("first", "second", "third", "then", "next", "after that", "finally", "lastly",
            "step", "to start", "begin by", "also", "additionally", "for example",
            "for instance", "in addition", "overall")
EXAMPLE = ("for example", "for instance", "e.g", "such as", "like when", "in my project",
           "i used", "i built")


@lru_cache(maxsize=2048)
def _kw_re(keyword: str) -> re.Pattern[str]:
    kw = re.escape(keyword.lower())
    # prefix-match for stems ("chunk" -> "chunking"); exact word for very short keywords
    tail = r"\b" if len(keyword) <= 3 else ""
    return re.compile(r"(?<![a-z0-9])" + kw + tail)


def _has(keyword: str, text: str) -> bool:
    return bool(_kw_re(keyword).search(text))


def _count_phrases(phrases: tuple[str, ...], text: str) -> Counter[str]:
    c: Counter[str] = Counter()
    for p in phrases:
        n = len(re.findall(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", text))
        if n:
            c[p] = n
    return c


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _content_tokens(text: str) -> set[str]:
    return {t for t in _tokens(text) if len(t) > 3 and t not in _STOP}


def _keywords_for(point: ExpectedPoint) -> list[str]:
    if point.keywords:
        return point.keywords
    return sorted(_content_tokens(point.description))[:6]


def _sentences(text: str) -> list[str]:
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    return parts or [text.strip()]


def coverage(question: Question, answer: str) -> tuple[list[ExpectedPoint], list[ExpectedPoint]]:
    """Split the question's expected points into (touched, not touched) by the answer."""
    text = answer.lower()
    matched: list[ExpectedPoint] = []
    missed: list[ExpectedPoint] = []
    for p in question.expected_points:
        hit = any(_has(k, text) for k in _keywords_for(p))
        (matched if hit else missed).append(p)
    return matched, missed


def _band(value: float, cuts: tuple[float, float, float, float]) -> int:
    """Map ``value`` to 1..5 using ascending cut-points."""
    return 1 + sum(value >= c for c in cuts)


def heuristic_score(question: Question, answer: str) -> RubricScore:
    text = answer.strip().lower()
    toks = _tokens(text)
    n = len(toks)
    sents = _sentences(answer)
    n_sent = len(sents)

    points = question.expected_points
    matched: list[ExpectedPoint] = []
    missed: list[ExpectedPoint] = []
    kw_hits_total = 0
    for p in points:
        hits = [k for k in _keywords_for(p) if _has(k, text)]
        kw_hits_total += len(hits)
        (matched if hits else missed).append(p)
    ratio = len(matched) / len(points) if points else 0.5

    hedges = _count_phrases(HEDGES, text)
    fillers = _count_phrases(FILLERS, text)
    vague = _count_phrases(VAGUE, text)
    connectors = _count_phrases(CONNECTORS, text)
    sequence = _count_phrases(SEQUENCE, text)
    n_hedge_fill = sum(hedges.values()) + sum(fillers.values())
    density = n_hedge_fill / n if n else 0.0
    vague_density = sum(vague.values()) / n if n else 0.0
    digits = len(re.findall(r"\d", text))
    skills_named = len(extract_skills(answer))
    code_like = len(re.findall(r"[a-z_]+\(\)|--[a-z-]+|\b[a-z]+_[a-z_]+\b|`[^`]+`", text))
    specifics = min(digits, 3) + skills_named + code_like
    has_example = any(e in text for e in EXAMPLE)
    unique_ratio = len(set(toks)) / n if n else 1.0
    no_idea = bool(re.search(r"\b(no idea|i don'?t know|dunno|not sure)\b", text)) and n < 25

    stuffing = n >= 12 and kw_hits_total / n > 0.30 and not connectors and n_sent <= 2

    # ---- correctness: coverage of expected points
    cov_cuts = (1e-9, 0.26, 0.51, 0.76)
    correctness = _band(ratio, cov_cuts)
    if n < 12:
        correctness = min(correctness, 2)
    if density > 0.08:
        correctness -= 1
    if no_idea:
        correctness = 1
    if stuffing:
        correctness = min(correctness, 3)
    correctness = max(1, min(5, correctness))

    # ---- depth: length + specifics + reasoning + example (capped when coverage is poor)
    depth_pts = (
        min(n / 50, 2.0)
        + min(specifics, 4) * 0.4
        + min(sum(connectors.values()), 3) * 0.5
        + (0.5 if has_example else 0.0)
    )
    depth = _band(depth_pts, (1.0, 2.0, 3.2, 4.4))
    if ratio < 0.26:
        depth = min(depth, 2)
    elif ratio < 0.51:
        depth = min(depth, 3)
    if stuffing:
        depth = min(depth, 2)

    # ---- clarity: directness, sentence length, hedging, vagueness
    clarity = 5
    if density > 0.08:
        clarity -= 2
    elif density > 0.03:
        clarity -= 1
    if n < 8:
        clarity -= 3
    elif n < 20:
        clarity -= 1
    if n_sent and n / n_sent > 32:
        clarity -= 1
    if n > 25 and unique_ratio < 0.55:
        clarity -= 1
    if vague_density > 0.03:
        clarity -= 1
    if stuffing:
        clarity -= 2
    clarity = max(1, min(5, clarity))

    # ---- structure: sequencing, multiple sentences, STAR for behavioural questions
    star_hits = 0
    if question.category == Category.BEHAVIORAL:
        star_hits = sum(any(_has(k, text) for k in kws) for _, kws in STAR_POINTS)
        structure = min(5, 1 + star_hits)
    else:
        markers = len(sequence) + len(connectors)
        structure = 1 + (n_sent >= 2) + (n_sent >= 4) + (markers >= 2) + (markers >= 4)
    if n_sent == 1 and n > 40:
        structure = min(structure, 2)
    if stuffing:
        structure = 1
    structure = max(1, min(5, structure))

    # ---- relevance: stays on the question's topic
    q_tokens = _content_tokens(question.text + " " + question.topic)
    overlap = len(_content_tokens(answer) & q_tokens) / max(1, min(len(q_tokens), 8))
    rel_value = 0.65 * ratio + 0.35 * min(1.0, overlap)
    relevance = _band(rel_value, (0.10, 0.30, 0.50, 0.70))
    if n < 8:
        relevance = min(relevance, 2)
    if no_idea:
        relevance = 1

    return RubricScore(
        correctness=DimensionScore(
            score=correctness, feedback=_fb_correctness(matched, missed, points, no_idea)
        ),
        depth=DimensionScore(
            score=depth,
            feedback=_fb_depth(n, specifics, sum(connectors.values()), has_example, ratio),
        ),
        clarity=DimensionScore(
            score=clarity, feedback=_fb_clarity(hedges, fillers, vague, n, n_sent, stuffing)
        ),
        structure=DimensionScore(
            score=structure,
            feedback=_fb_structure(question, text, n_sent, len(sequence) + len(connectors)),
        ),
        relevance=DimensionScore(score=relevance, feedback=_fb_relevance(question, relevance)),
        overall_feedback=_overall(correctness, depth, clarity, structure, relevance),
        sample_answer=sample_answer(question),
    )


# --------------------------------------------------------------------------- feedback text


def _fb_correctness(matched: list[ExpectedPoint], missed: list[ExpectedPoint],
                    points: list[ExpectedPoint], no_idea: bool) -> str:
    if no_idea:
        return "You said you were unsure. It is fine to say so, but follow with how you would find out."
    if not points:
        return "No reference points were available for this question."
    msg = f"You touched {len(matched)} of {len(points)} expected points."
    if missed:
        msg += " Missing: " + "; ".join(p.description for p in missed[:3]) + "."
    else:
        msg += " Nothing important was left out."
    return msg


def _fb_depth(n: int, specifics: int, connectors: int, has_example: bool, ratio: float) -> str:
    gaps = []
    if specifics < 2:
        gaps.append("name concrete tools, numbers or commands")
    if connectors < 1:
        gaps.append("explain *why* with a trade-off or reason ('because...', 'instead of...')")
    if not has_example:
        gaps.append("add a short example from your own work")
    if n < 40:
        gaps.append("expand: the answer is very brief")
    if ratio < 0.26 and n >= 40:
        gaps.append("the length is not matched by relevant content")
    if not gaps:
        return f"Good depth: ~{n} words with specifics, reasoning and an example."
    return "To go deeper: " + "; ".join(gaps) + "."


def _fb_clarity(hedges: Counter[str], fillers: Counter[str], vague: Counter[str], n: int,
                n_sent: int, stuffing: bool) -> str:
    notes = []
    flagged = {**hedges, **fillers}
    if flagged:
        top = ", ".join(f"'{k}' x{v}" for k, v in Counter(flagged).most_common(3))
        notes.append(f"Hedging/filler detected ({top}); say it directly.")
    if vague:
        notes.append("Vague words (" + ", ".join(vague) + ") hide the specifics; name the thing.")
    if n < 20:
        notes.append("Too short to be clearly communicated; give at least two or three sentences.")
    if n_sent and n / n_sent > 32:
        notes.append("Sentences are long; split them.")
    if stuffing:
        notes.append("This reads like a keyword list rather than an explanation.")
    return " ".join(notes) if notes else "Clear and direct."


def _fb_structure(question: Question, text: str, n_sent: int, markers: int) -> str:
    if question.category == Category.BEHAVIORAL:
        marks = []
        for label, kws in zip(("Situation", "Task", "Action", "Result", "Reflection"),
                              STAR_POINTS, strict=True):
            marks.append(f"{label} {'✓' if any(_has(k, text) for k in kws[1]) else '✗'}")
        return "STAR coverage: " + ", ".join(marks) + "."
    if n_sent < 2:
        return "Break the answer into steps: a one-line summary, the reasoning, then an example."
    if markers < 2:
        return "Add signposts (first / then / because / finally) so the listener can follow."
    return "Well organised: the answer moves through its points in order."


def _fb_relevance(question: Question, score: int) -> str:
    if score >= 4:
        return "Stays on the question."
    if score == 3:
        return f"Partly on topic; tie more of the answer back to {question.topic}."
    return f"Drifts from what was asked; address {question.topic} directly before adding detail."


def _overall(c: int, d: int, cl: int, s: int, r: int) -> str:
    scores = {"correctness": c, "depth": d, "clarity": cl, "structure": s, "relevance": r}
    best = max(scores, key=lambda k: scores[k])
    worst = min(scores, key=lambda k: scores[k])
    if scores[best] == scores[worst]:
        return f"Consistent across the rubric ({scores[best]}/5 on every dimension)."
    return (f"Strongest: {best} ({scores[best]}/5). Biggest opportunity: {worst} "
            f"({scores[worst]}/5), focus your next attempt there.")


def sample_answer(question: Question) -> str:
    """Offline stand-in for a model-written exemplar, assembled from the expected points."""
    pts = [p.description for p in question.expected_points]
    if question.category == Category.BEHAVIORAL:
        return (
            "A strong STAR answer would: set the situation in one or two sentences; state the "
            "specific task you owned; describe the concrete actions *you* took and why; give a "
            "measurable result; and close with what you would do differently next time."
        )
    if not pts:
        return "A strong answer defines the idea, gives a concrete example, and states a trade-off."
    body = "; ".join(pts[:-1]) + (f"; and {pts[-1]}" if len(pts) > 1 else pts[0])
    return (f"A strong answer would open with a one-line summary, then cover: {body}. "
            "It would close with a short example from your own work and one trade-off.")
