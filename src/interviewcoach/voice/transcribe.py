"""Speech-to-text backends: OpenAI-compatible Whisper API, or local faster-whisper.

Neither backend is exercised by the offline test-suite (they need a key or a model download);
only the metrics in ``voice.metrics`` are unit-tested. See the README for what has and has not
been verified end to end.
"""

from __future__ import annotations

import io
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..config import Settings
from .metrics import wav_duration


@dataclass(frozen=True)
class Transcript:
    text: str
    duration_s: float | None


class Transcriber(Protocol):
    def transcribe(self, audio: bytes, filename: str = "answer.wav") -> Transcript: ...


class WhisperAPITranscriber:
    """Whisper through an OpenAI-compatible ``/audio/transcriptions`` endpoint."""

    def __init__(self, api_key: str | None, base_url: str | None, model: str = "whisper-1",
                 client: Any | None = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key or "not-needed", base_url=base_url)
        self._client = client
        self.model = model

    def transcribe(self, audio: bytes, filename: str = "answer.wav") -> Transcript:
        buf = io.BytesIO(audio)
        buf.name = filename
        resp = self._client.audio.transcriptions.create(
            model=self.model, file=buf, response_format="verbose_json"
        )
        duration = getattr(resp, "duration", None) or wav_duration(audio)
        return Transcript(text=str(resp.text).strip(), duration_s=duration)


class LocalWhisperTranscriber:
    """Fully local transcription with faster-whisper (``pip install 'interviewcoach[voice]'``)."""

    def __init__(self, model_size: str = "base.en") -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Run: pip install 'interviewcoach[voice]'"
            ) from exc
        self._model = WhisperModel(model_size, compute_type="int8")

    def transcribe(self, audio: bytes, filename: str = "answer.wav") -> Transcript:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.write_bytes(audio)
            segments, info = self._model.transcribe(str(path), vad_filter=True)
            text = " ".join(seg.text.strip() for seg in segments).strip()
        return Transcript(text=text, duration_s=getattr(info, "duration", None) or wav_duration(audio))


def get_transcriber(settings: Settings) -> Transcriber | None:
    if settings.stt_backend == "api":
        return WhisperAPITranscriber(settings.api_key, settings.base_url, settings.stt_api_model)
    if settings.stt_backend == "local":
        return LocalWhisperTranscriber(settings.whisper_model)
    return None
