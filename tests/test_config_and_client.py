from __future__ import annotations

from types import SimpleNamespace

import pytest

from interviewcoach.config import Settings
from interviewcoach.llm import MockLLM, OpenAICompatClient, get_llm
from interviewcoach.llm.base import LLMError, LLMRequest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("LLM_PROVIDER", "LLM_API_KEY", "OPENAI_API_KEY", "LLM_BASE_URL", "LLM_MODEL",
              "INTERVIEWCOACH_DB", "STT_BACKEND"):
        monkeypatch.delenv(k, raising=False)


def test_defaults_to_mock_without_a_key():
    s = Settings.from_env(load_dotenv_file=False)
    assert s.is_mock and isinstance(get_llm(s), MockLLM)


def test_key_switches_to_live_provider(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "my-model")
    s = Settings.from_env(load_dotenv_file=False)
    assert s.provider == "openai" and s.model == "my-model" and s.llm_label == "my-model"


def test_explicit_mock_wins_over_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    assert Settings.from_env(load_dotenv_file=False).is_mock


def test_live_without_key_or_base_url_is_an_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        Settings.from_env(load_dotenv_file=False)
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")  # local server needs no key
    assert Settings.from_env(load_dotenv_file=False).base_url


def test_unknown_provider_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "carrier-pigeon")
    with pytest.raises(ValueError):
        Settings.from_env(load_dotenv_file=False)


def test_db_path_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("INTERVIEWCOACH_DB", str(tmp_path / "x.db"))
    assert Settings.from_env(load_dotenv_file=False).db_path == tmp_path / "x.db"


def _fake_client(content=None, fail_first_with=None):
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        if fail_first_with and len(calls) == 1:
            raise RuntimeError(fail_first_with)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return client, calls


REQ = LLMRequest(task="score", system="sys", user="usr")


def test_openai_client_sends_messages_and_json_mode():
    client, calls = _fake_client('{"ok": true}')
    out = OpenAICompatClient("m", client=client).complete(REQ)
    assert out == '{"ok": true}'
    assert calls[0]["messages"][0] == {"role": "system", "content": "sys"}
    assert calls[0]["response_format"] == {"type": "json_object"}


def test_openai_client_retries_without_response_format_when_unsupported():
    client, calls = _fake_client('{"ok": 1}', fail_first_with="unsupported response_format")
    assert OpenAICompatClient("m", client=client).complete(REQ) == '{"ok": 1}'
    assert "response_format" not in calls[1]


def test_openai_client_wraps_errors_and_empty_replies():
    client, _ = _fake_client(fail_first_with="boom")
    with pytest.raises(LLMError, match="boom"):
        OpenAICompatClient("m", client=client).complete(REQ)
    client, _ = _fake_client("")
    with pytest.raises(LLMError, match="empty"):
        OpenAICompatClient("m", client=client).complete(REQ)
