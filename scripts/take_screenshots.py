"""Drive the real Streamlit app with a real browser (system Chrome via Playwright) and save
screenshots. Requires:  pip install -e '.[screenshots]'  and Google Chrome installed.

Uses mock LLM mode and a throw-away database, so every screenshot is a genuine run of the app.
The Progress screenshot is taken from a database filled by `interviewcoach demo`.

    python scripts/take_screenshots.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
WORK = ROOT / ".demo"
APP = ROOT / "src" / "interviewcoach" / "ui" / "app.py"


def serve(port: int, db: Path) -> subprocess.Popen[bytes]:
    env = {**os.environ, "LLM_PROVIDER": "mock", "INTERVIEWCOACH_DB": str(db)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(APP), "--server.port", str(port),
         "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://localhost:{port}/_stcore/health", timeout=1)
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    raise RuntimeError("streamlit did not start")


def snap(page: Page, name: str, full: bool = True) -> None:
    page.wait_for_timeout(800)
    if full:
        page.screenshot(path=str(OUT / name), full_page=True)
    else:  # crop the empty space below short pages
        page.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": 1280, "height": 760})
    print("saved", name)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    answers = json.loads((ROOT / "examples" / "demo_answers.json").read_text())["sessions"]
    fresh = WORK / "shots_fresh.db"
    demo = WORK / "shots_demo.db"
    for p in (fresh, demo):
        p.unlink(missing_ok=True)
    env = {**os.environ, "LLM_PROVIDER": "mock", "INTERVIEWCOACH_DB": str(demo)}
    subprocess.run([sys.executable, "-m", "interviewcoach.cli", "demo", "--voice"],
                   cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)

    a, b = serve(8611, fresh), serve(8612, demo)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="chrome", headless=True)
            ctx = browser.new_context(viewport={"width": 1280, "height": 1500},
                                      device_scale_factor=1.5)
            page = ctx.new_page()
            page.goto("http://localhost:8611")
            page.get_by_text("Resume and job description").first.wait_for()
            page.get_by_role("button", name="Use the bundled sample resume").click()
            page.get_by_text("Resume loaded").wait_for()
            page.get_by_role("button", name="Analyze fit").click()
            page.get_by_text("Skills gap for").wait_for()
            snap(page, "01-setup-gap-analysis.png")

            page.get_by_role("button", name="Start interview").click()
            page.get_by_text("Question 1 of").wait_for()
            snap(page, "02-interview-question.png", full=False)

            box = page.get_by_label("Your answer")
            box.fill(answers["third"]["project:PromptShield"])
            box.press("Control+Enter")
            page.get_by_role("button", name="Submit answer").click()
            page.get_by_text("Feedback on your last answer").wait_for()
            snap(page, "03-answer-feedback.png")

            page2 = ctx.new_page()
            page2.goto("http://localhost:8612")
            page2.get_by_text("Resume and job description").first.wait_for()
            page2.get_by_text("Progress", exact=True).first.click()
            page2.get_by_text("Score trend by category").wait_for()
            page2.wait_for_timeout(1500)
            snap(page2, "04-progress-dashboard.png")
            page2.get_by_text("Privacy", exact=True).first.click()
            page2.get_by_text("Privacy and your data").wait_for()
            snap(page2, "05-privacy-delete.png", full=False)
            browser.close()
    finally:
        a.terminate()
        b.terminate()


if __name__ == "__main__":
    main()
