from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from interviewcoach import cli
from interviewcoach.db import Database

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "src" / "interviewcoach" / "ui" / "app.py")


@pytest.fixture()
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("INTERVIEWCOACH_DB", str(tmp_path / "app.db"))
    import streamlit as st

    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def button(at: AppTest, label: str):
    return next(b for b in at.button if label in b.label)


def test_footer_credits_author_on_every_page(app):
    for page in ("Setup", "Interview", "Progress", "Privacy"):
        app.session_state["nav"] = page
        app.run()
        assert not app.exception
        html = " ".join(m.value for m in app.markdown)
        assert "Built by" in html and "github.com/Aryaveer009" in html and "Aryaveer Mankotia" in html


def test_end_to_end_flow_and_delete_my_data(app):
    button(app, "bundled sample").click().run()
    button(app, "Analyze fit").click().run()
    assert not app.exception
    assert any("Skills gap" in s.value for s in app.subheader)

    button(app, "Start interview").click().run()
    assert app.session_state["nav"] == "Interview"
    app.text_area[0].set_value("I chose YAML attacks because it is easy to extend.").run()
    button(app, "Submit answer").click().run()
    assert not app.exception
    assert any("Feedback on your last answer" in m.value for m in app.markdown)

    app.session_state["nav"] = "Progress"
    app.run()
    assert not app.exception and any("Score trend" in s.value for s in app.subheader)

    app.session_state["nav"] = "Privacy"
    app.run()
    delete = button(app, "Delete my data")
    assert delete.disabled  # needs the confirmation checkbox first
    app.checkbox[0].check().run()
    button(app, "Delete my data").click().run()
    db = Database(os.environ["INTERVIEWCOACH_DB"])
    assert db.counts() == {"profiles": 0, "job_descriptions": 0, "sessions": 0, "turns": 0}
    assert "session" not in app.session_state


def test_cli_demo_and_eval(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("INTERVIEWCOACH_DB", str(tmp_path / "demo.db"))
    transcript = tmp_path / "t.md"
    rc = cli.main(["demo", "--answers", str(ROOT / "examples" / "demo_answers.json"),
                   "--sessions", "first", "third", "--voice", "--transcript", str(transcript)])
    assert rc == 0 and "Session `first`" in transcript.read_text()
    db = Database(tmp_path / "demo.db")
    sessions = db.sessions()
    assert len(sessions) == 2 and sessions[1]["avg_overall"] > sessions[0]["avg_overall"]
    assert all(t["wpm"] for t in db.turns())

    out = tmp_path / "eval.md"
    assert cli.main(["eval", "--evals", str(ROOT / "evals"), "--out", str(out)]) == 0
    assert "Pairwise correct" in out.read_text()
    json.dumps(capsys.readouterr().out)  # output is plain text
