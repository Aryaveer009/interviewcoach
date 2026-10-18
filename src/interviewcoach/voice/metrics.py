"""Speech delivery metrics: filler-word counter and speaking-pace feedback (pure Python)."""

from __future__ import annotations

import io
import re
import wave
from collections import Counter
from dataclasses import dataclass

# Unambiguous fillers, matched as whole words.
_SINGLE = ("um", "uh", "uhm", "umm", "er", "erm", "ah", "hmm", "basically", "literally",
           "actually")
# Multi-word fillers.
_PHRASES = ("you know", "i mean", "sort of", "kind of")
# "like" is only a filler when set off by commas (", like,"); otherwise it is a real word.
_LIKE_FILLER = re.compile(r"(?:,|\.\.\.|—)\s*like\s*(?:,|\.\.\.|—)", re.IGNORECASE)

IDEAL_WPM = (120, 160)


@dataclass(frozen=True)
class SpeechMetrics:
    words: int
    duration_s: float
    wpm: float
    filler_count: int
    fillers: dict[str, int]
    pace_label: str
    pace_feedback: str


def count_fillers(text: str) -> tuple[int, dict[str, int]]:
    low = text.lower()
    found: Counter[str] = Counter()
    for w in _SINGLE:
        n = len(re.findall(rf"(?<![a-z']){w}(?![a-z'])", low))
        if n:
            found[w] = n
    for ph in _PHRASES:
        n = len(re.findall(rf"(?<![a-z]){re.escape(ph)}(?![a-z])", low))
        if n:
            found[ph] = n
    n_like = len(_LIKE_FILLER.findall(text))
    if n_like:
        found["like"] = n_like
    return sum(found.values()), dict(found)


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", text))


def pace_feedback(wpm: float) -> tuple[str, str]:
    lo, hi = IDEAL_WPM
    if wpm < 90:
        return "very slow", f"{wpm:.0f} wpm is quite slow; aim for {lo}-{hi}. Cut pauses and trim detail."
    if wpm < lo:
        return "slow", f"{wpm:.0f} wpm is slightly slow; a little more energy ({lo}-{hi} wpm) sounds more confident."
    if wpm <= hi:
        return "good", f"{wpm:.0f} wpm is in the comfortable {lo}-{hi} range."
    if wpm <= 190:
        return "fast", f"{wpm:.0f} wpm is fast; slow down and pause between points ({lo}-{hi} wpm)."
    return "very fast", f"{wpm:.0f} wpm is very fast; interviewers will struggle to follow."


def analyze_speech(text: str, duration_s: float) -> SpeechMetrics:
    words = count_words(text)
    wpm = words / (duration_s / 60) if duration_s > 0 else 0.0
    total, detail = count_fillers(text)
    label, advice = pace_feedback(wpm) if duration_s > 0 else ("unknown", "No duration available.")
    return SpeechMetrics(words, round(duration_s, 2), round(wpm, 1), total, detail, label, advice)


def wav_duration(data: bytes) -> float | None:
    """Duration in seconds of WAV bytes (what Streamlit's audio recorder produces)."""
    try:
        with wave.open(io.BytesIO(data)) as w:
            return w.getnframes() / float(w.getframerate())
    except (wave.Error, EOFError):
        return None
