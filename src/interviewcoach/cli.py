"""Command line entry point: ``interviewcoach app | demo | eval``."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib import resources
from pathlib import Path

from .config import Settings
from .db import Database
from .evaluation import load_items, per_answer_table, render_markdown, run_eval
from .gap import analyze_gap
from .interview import InterviewSession
from .llm import get_llm
from .parsing import extract_text, parse_job_description, parse_resume
from .scoring import RubricScorer
from .voice.metrics import analyze_speech


def sample_dir() -> Path:
    return Path(str(resources.files("interviewcoach") / "sample_data"))


def _load_sample() -> tuple[object, object]:
    d = sample_dir()
    resume = parse_resume(extract_text((d / "resume.pdf").read_bytes(), "resume.pdf"))
    jd = parse_job_description((d / "job_description.txt").read_text(encoding="utf-8"))
    return resume, jd


def cmd_app(_: argparse.Namespace) -> int:
    app = Path(__file__).parent / "ui" / "app.py"
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)])


def cmd_demo(args: argparse.Namespace) -> int:
    """Run scripted sessions end to end (mock LLM unless env says otherwise)."""
    settings = Settings.from_env()
    db = Database(args.db or settings.db_path)
    llm = get_llm(settings)
    answers = json.loads(Path(args.answers).read_text(encoding="utf-8"))
    profile, jd = _load_sample()
    gap = analyze_gap(profile, jd)  # type: ignore[arg-type]
    transcript: list[str] = [f"# Demo sessions (LLM: {settings.llm_label})", ""]
    print(f"Gap coverage: {gap.coverage_pct}%")
    for name in args.sessions:
        script = answers["sessions"][name]
        session = InterviewSession.start(llm, db, profile, jd, gap,  # type: ignore[arg-type]
                                         llm_label=settings.llm_label)
        transcript += [f"## Session `{name}` (id {session.session_id})", ""]
        while not session.finished:
            q = session.current
            assert q is not None
            key = f"{q.category.value}:{q.topic}" if not q.is_followup else "followup"
            text = script.get(key) or script.get(q.category.value + ":*") or script["default"]
            speech = analyze_speech(text, len(text.split()) / 140 * 60) if args.voice else None
            result = session.submit(
                text,
                filler_count=speech.filler_count if speech else None,
                wpm=speech.wpm if speech else None,
            )
            s = result.score
            tag = f"follow-up ({q.followup_kind})" if q.is_followup else q.category.value
            transcript += [
                f"**[{tag}] {q.text}**", "", f"> {text}", "",
                f"Scores: {s.dimension_scores()} → **{s.overall}/5**", "",
                f"- {s.overall_feedback}", "",
            ]
            print(f"  [{tag:<22}] {q.topic:<18} overall {s.overall}")
        summ = session.summary()
        transcript += [f"**Session summary:** {summ}", ""]
        print(f"session {name}: {summ}")
    if args.transcript:
        Path(args.transcript).write_text("\n".join(transcript), encoding="utf-8")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    llm = get_llm(settings)
    root = Path(args.evals)
    items = load_items(root / "answers_dev.json", root / "answers_heldout.json")
    report = run_eval(RubricScorer(llm), items)
    label = settings.llm_label
    md = render_markdown(report, label)
    print(md)
    if args.out:
        out = Path(args.out)
        out.write_text(
            md + "\n\n### Every scored answer\n\n" + per_answer_table(report) + "\n",
            encoding="utf-8",
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="interviewcoach", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("app", help="launch the Streamlit app").set_defaults(func=cmd_app)

    d = sub.add_parser("demo", help="run scripted demo sessions on the bundled sample")
    d.add_argument("--answers", default="examples/demo_answers.json")
    d.add_argument("--sessions", nargs="+", default=["first", "second", "third"])
    d.add_argument("--db", default=None, help="SQLite path (default: INTERVIEWCOACH_DB)")
    d.add_argument("--transcript", default=None, help="write a markdown transcript here")
    d.add_argument("--voice", action="store_true", help="simulate spoken-answer metrics")
    d.set_defaults(func=cmd_demo)

    e = sub.add_parser("eval", help="evaluate the scorer on the good/mediocre/bad answer set")
    e.add_argument("--evals", default="evals")
    e.add_argument("--out", default=None, help="write the markdown report here")
    e.set_defaults(func=cmd_eval)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
