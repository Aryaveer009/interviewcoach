"""InterviewCoach Streamlit app.  Run with:  streamlit run src/interviewcoach/ui/app.py"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from interviewcoach.cli import sample_dir
from interviewcoach.config import AUTHOR_NAME, AUTHOR_URL, Settings
from interviewcoach.db import Database
from interviewcoach.gap import analyze_gap
from interviewcoach.interview import InterviewSession
from interviewcoach.llm import LLMClient, get_llm
from interviewcoach.models import DIMENSIONS, GapStatus
from interviewcoach.parsing import ParseError, extract_text, parse_job_description, parse_resume
from interviewcoach.progress import (
    category_trend,
    dimension_averages,
    speech_summary,
    turns_frame,
    weakest_topics,
)
from interviewcoach.voice import analyze_speech, get_transcriber, wav_duration

st.set_page_config(page_title="InterviewCoach", page_icon="🎯", layout="wide")

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1100px;}
.ic-card {border: 1px solid rgba(128,128,128,.25); border-radius: 14px; padding: 1.1rem 1.3rem;
          background: rgba(99,102,241,.06);}
.ic-badge {display:inline-block; padding: .15rem .6rem; border-radius: 999px; font-size: .75rem;
           font-weight: 600; letter-spacing: .03em; background:#6366f1; color:white;}
.ic-badge.followup {background:#f59e0b;}
.ic-q {font-size: 1.15rem; line-height: 1.55; margin-top: .6rem;}
.ic-footer {text-align:center; opacity:.75; margin-top: 3rem; padding-top: 1rem;
            border-top: 1px solid rgba(128,128,128,.25); font-size:.9rem;}
.ic-footer a {color:#6366f1; text-decoration:none; font-weight:600;}
</style>
"""
STATUS_ICON = {GapStatus.COVERED: "🟢 covered", GapStatus.PARTIAL: "🟡 partial",
               GapStatus.MISSING: "🔴 missing"}


@st.cache_resource
def _settings() -> Settings:
    return Settings.from_env()


@st.cache_resource
def _db(path: str) -> Database:
    return Database(path)


@st.cache_resource
def _llm(_settings_obj: Settings) -> LLMClient:
    return get_llm(_settings_obj)


def goto(page: str) -> None:
    st.session_state["nav"] = page


# --------------------------------------------------------------------------- pages


def page_setup(settings: Settings, db: Database, llm: LLMClient) -> None:
    st.header("1 · Resume and job description")
    left, right = st.columns(2)
    with left:
        upload = st.file_uploader("Resume (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"])
        if st.button("Use the bundled sample resume + job description"):
            d = sample_dir()
            st.session_state["resume_file"] = ("resume.pdf", (d / "resume.pdf").read_bytes())
            st.session_state["jd_text"] = (d / "job_description.txt").read_text(encoding="utf-8")
            st.session_state.pop("analysis", None)
        if upload is not None:
            st.session_state["resume_file"] = (upload.name, upload.getvalue())
        if "resume_file" in st.session_state:
            st.caption(f"Resume loaded: **{st.session_state['resume_file'][0]}**")
    with right:
        jd_text = st.text_area("Job description", value=st.session_state.get("jd_text", ""),
                               height=250, placeholder="Paste the job description here…")

    if st.button("Analyze fit", type="primary"):
        if "resume_file" not in st.session_state or not jd_text.strip():
            st.warning("Add a resume and a job description first.")
        else:
            try:
                name, data = st.session_state["resume_file"]
                profile = parse_resume(extract_text(data, name))
                jd = parse_job_description(jd_text)
                st.session_state["analysis"] = (profile, jd, analyze_gap(profile, jd))
                st.session_state["jd_text"] = jd_text
            except ParseError as exc:
                st.error(str(exc))

    if "analysis" not in st.session_state:
        return
    profile, jd, gap = st.session_state["analysis"]
    st.subheader(f"Skills gap for **{jd.title or 'this role'}**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Weighted coverage", f"{gap.coverage_pct}%")
    c2.metric("Covered", len(gap.by_status(GapStatus.COVERED)))
    c3.metric("Partly covered", len(gap.by_status(GapStatus.PARTIAL)))
    c4.metric("Missing", len(gap.by_status(GapStatus.MISSING)))
    st.dataframe(
        pd.DataFrame(
            [{"Skill": i.skill, "Importance": i.importance, "Status": STATUS_ICON[i.status],
              "Evidence": i.evidence or "–"} for i in gap.items]
        ),
        hide_index=True, use_container_width=True,
    )
    with st.expander(f"What was parsed from the resume ({len(profile.projects)} projects)"):
        st.write(f"**Name:** {profile.name}  ·  **Skills found:** {', '.join(profile.skills)}")
        for p in profile.projects:
            st.markdown(f"**{p.name}**: {', '.join(p.skills) or 'no skills detected'}")

    st.subheader("2 · Interview settings")
    s1, s2, s3 = st.columns(3)
    n_tech = s1.slider("Technical questions", 0, 5, 3)
    n_proj = s2.slider("Project deep-dives", 0, 3, 2)
    n_beh = s3.slider("Behavioural (STAR)", 0, 4, 2)
    follow = st.checkbox("Adaptive follow-ups", value=True)

    def start() -> None:
        session = InterviewSession.start(
            llm, db, profile, jd, gap, llm_label=settings.llm_label, n_technical=n_tech,
            n_project=n_proj, n_behavioral=n_beh, max_followups=1 if follow else 0,
        )
        st.session_state["session"] = session
        st.session_state["last_result"] = None
        goto("Interview")

    if n_tech + n_proj + n_beh == 0:
        st.info("Choose at least one question.")
    else:
        st.button("Start interview →", type="primary", on_click=start)


def _render_score(result) -> None:
    s = result.score
    st.markdown(f"#### Feedback on your last answer: **{s.overall} / 5**")
    cols = st.columns(len(DIMENSIONS))
    for col, dim in zip(cols, DIMENSIONS, strict=True):
        col.metric(dim.capitalize(), f"{getattr(s, dim).score} / 5")
    for dim in DIMENSIONS:
        st.markdown(f"- **{dim.capitalize()}**: {getattr(s, dim).feedback}")
    st.info(s.overall_feedback)
    with st.expander("A stronger sample answer"):
        st.write(s.sample_answer)
    meta = st.session_state.get("last_speech")
    if meta:
        st.caption(f"🎙️ {meta.words} words · {meta.wpm} wpm ({meta.pace_label}): "
                   f"{meta.pace_feedback}  ·  filler words: {meta.filler_count} {meta.fillers or ''}")


def page_interview(settings: Settings) -> None:
    st.header("Interview")
    session: InterviewSession | None = st.session_state.get("session")
    if session is None:
        st.info("Set up a resume and job description first.")
        st.button("Go to setup", on_click=goto, args=("Setup",))
        return

    last = st.session_state.get("last_result")
    if last is not None:
        _render_score(last)
        st.divider()

    if session.finished:
        summary = session.summary()
        st.success(f"Interview complete · average score {summary['overall']} / 5 "
                   f"over {summary['turns']} answers")
        st.json(summary["by_category"])
        st.button("See progress dashboard →", on_click=goto, args=("Progress",))
        return

    q = session.current
    assert q is not None
    st.progress(min(1.0, session.main_done / max(1, session.total_main)),
                text=f"Question {min(session.main_done + 1, session.total_main)} of "
                     f"{session.total_main}")
    badge_cls = "ic-badge followup" if q.is_followup else "ic-badge"
    label = f"follow-up · {q.followup_kind}" if q.is_followup else q.category.value
    st.markdown(
        f"<div class='ic-card'><span class='{badge_cls}'>{label.upper()}</span>"
        f"<div class='ic-q'>{q.text}</div></div>",
        unsafe_allow_html=True,
    )

    idx = len(session.results)
    key = f"answer_{idx}"
    transcriber = get_transcriber(settings) if settings.stt_backend != "off" else None
    if transcriber is not None:
        audio = st.audio_input("🎙️ Or record your answer")
        if audio is not None and st.button("Transcribe recording"):
            data = audio.getvalue()
            with st.spinner("Transcribing…"):
                t = transcriber.transcribe(data)
            st.session_state[key] = t.text
            st.session_state["pending_duration"] = t.duration_s or wav_duration(data)
    answer = st.text_area("Your answer", key=key, height=180)

    if st.button("Submit answer", type="primary"):
        if not answer.strip():
            st.warning("Type or record an answer first (or it will be scored as skipped).")
        duration = st.session_state.pop("pending_duration", None)
        speech = analyze_speech(answer, duration) if duration else None
        with st.spinner("Scoring…"):
            result = session.submit(
                answer, filler_count=speech.filler_count if speech else None,
                wpm=speech.wpm if speech else None,
            )
        st.session_state["last_result"] = result
        st.session_state["last_speech"] = speech
        st.rerun()


def page_progress(db: Database) -> None:
    st.header("Progress")
    df = turns_frame(db)
    if df.empty:
        st.info("No sessions yet. Finish an interview and your trends will appear here.")
        return
    sessions = db.sessions()
    c1, c2, c3 = st.columns(3)
    c1.metric("Sessions", len(sessions))
    c2.metric("Answers scored", len(df))
    c3.metric("Average score", f"{df['overall'].mean():.2f} / 5")

    st.subheader("Score trend by category")
    trend = category_trend(df)
    trend.index = [f"Session {i}" for i in trend.index]
    st.line_chart(trend)
    st.caption("Average overall score (1–5) per session. Each point averages that session's "
               "answers in the category, follow-ups included.")

    left, right = st.columns(2)
    with left:
        st.subheader("Rubric dimensions (weakest first)")
        st.bar_chart(dimension_averages(df))
    with right:
        st.subheader("Weakest areas → practise next")
        for s in weakest_topics(df):
            st.markdown(f"**{s.topic}** ({s.category}) · avg {s.avg_score}/5  \n"
                        f"Weakest dimension: *{s.weakest_dimension}*. Try to {s.advice}.")
    speech = speech_summary(df)
    if speech:
        st.subheader("Speaking")
        st.write(f"{int(speech['answers'])} spoken answers · average pace "
                 f"**{speech['avg_wpm']} wpm** · average **{speech['avg_fillers']}** filler words "
                 "per answer")
    with st.expander("All sessions"):
        st.dataframe(pd.DataFrame(sessions), hide_index=True, use_container_width=True)


def page_privacy(settings: Settings, db: Database) -> None:
    st.header("Privacy and your data")
    if settings.is_mock:
        st.success("Mock mode: nothing you type leaves this machine; no network calls are made.")
    else:
        where = settings.base_url or "the OpenAI API"
        st.warning(f"Live mode: your answers and a resume summary are sent to **{where}** for "
                   "question writing and scoring. Use mock mode (or a local model) to keep "
                   "everything on your machine.")
    st.markdown(
        f"- Resumes are parsed **in memory**; the uploaded file is never written to disk.\n"
        f"- Only the parsed structure (no raw resume text), your answers and scores are stored, "
        f"in one local SQLite file: `{db.path}`.\n- No analytics, no telemetry, no cloud storage."
    )
    counts = db.counts()
    st.write("Currently stored:", counts)
    confirm = st.checkbox("I understand this permanently erases all my sessions and parsed resumes")
    if st.button("🗑️ Delete my data", disabled=not confirm, type="primary"):
        db.delete_all()
        for k in ("session", "last_result", "analysis", "resume_file", "jd_text", "last_speech"):
            st.session_state.pop(k, None)
        st.success("All data erased and the database file compacted.")
        st.rerun()


# --------------------------------------------------------------------------- main


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    settings = _settings()
    db = _db(str(settings.db_path))
    llm = _llm(settings)

    with st.sidebar:
        st.title("🎯 InterviewCoach")
        st.caption("Mock interviews tailored to your resume and the job.")
        st.radio("Navigate", ["Setup", "Interview", "Progress", "Privacy"], key="nav",
                 label_visibility="collapsed")
        st.divider()
        st.caption(f"LLM: **{settings.llm_label}**")
        st.caption(f"Data: `{Path(db.path).name}` (local)")

    page = st.session_state.get("nav", "Setup")
    if page == "Setup":
        page_setup(settings, db, llm)
    elif page == "Interview":
        page_interview(settings)
    elif page == "Progress":
        page_progress(db)
    else:
        page_privacy(settings, db)

    st.markdown(
        f"<div class='ic-footer'>Built by <a href='{AUTHOR_URL}' target='_blank'>{AUTHOR_NAME}</a>"
        "</div>",
        unsafe_allow_html=True,
    )


main()
