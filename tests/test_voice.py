from __future__ import annotations

import io
import wave
from types import SimpleNamespace

import pytest

from interviewcoach.config import Settings
from interviewcoach.voice import analyze_speech, count_fillers, get_transcriber, pace_feedback
from interviewcoach.voice.metrics import count_words, wav_duration
from interviewcoach.voice.transcribe import WhisperAPITranscriber


def wav_bytes(seconds: float, rate: int = 8000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))
    return buf.getvalue()


def test_filler_counter_counts_words_and_phrases():
    total, detail = count_fillers("Um, so basically you know it is, like, uh, actually fine. "
                                  "I mean, sort of.")
    assert detail == {"um": 1, "uh": 1, "basically": 1, "actually": 1, "you know": 1,
                      "i mean": 1, "sort of": 1, "like": 1}
    assert total == 8


def test_like_only_counts_when_set_off_by_commas():
    assert count_fillers("I would like to use it, like a cache.")[0] == 0
    assert count_fillers("It was, like, huge.")[1] == {"like": 1}


def test_filler_words_are_not_matched_inside_other_words():
    assert count_fillers("The umbrella is in the summer yummy-uhh")[0] == 0
    assert count_fillers("Her answer was errant")[0] == 0


@pytest.mark.parametrize(
    ("wpm", "label"),
    [(60, "very slow"), (105, "slow"), (140, "good"), (175, "fast"), (230, "very fast")],
)
def test_pace_labels(wpm, label):
    assert pace_feedback(wpm)[0] == label


def test_analyze_speech_computes_wpm_from_duration():
    text = " ".join(["word"] * 140)
    m = analyze_speech(text, 60.0)
    assert m.words == 140 and m.wpm == 140.0 and m.pace_label == "good"
    assert analyze_speech("hello there", 0).pace_label == "unknown"


def test_count_words_handles_punctuation():
    assert count_words("It's well-known, isn't it? Yes.") == 5


def test_wav_duration():
    assert wav_duration(wav_bytes(2.5)) == pytest.approx(2.5, abs=0.01)
    assert wav_duration(b"not audio") is None


def test_api_transcriber_uses_client_and_falls_back_to_wav_duration():
    calls = {}

    def create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(text=" hello world ", duration=None)

    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create)))
    t = WhisperAPITranscriber(None, None, "whisper-1", client=client).transcribe(wav_bytes(1.0))
    assert t.text == "hello world" and t.duration_s == pytest.approx(1.0, abs=0.01)
    assert calls["model"] == "whisper-1" and calls["response_format"] == "verbose_json"


def test_get_transcriber_off_by_default(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("STT_BACKEND", raising=False)
    assert get_transcriber(Settings.from_env(load_dotenv_file=False)) is None
