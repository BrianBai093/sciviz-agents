"""Record a video of the UI replaying a session (no API key, no LLM calls), then interact with the views.

Usage: uv run python demo/record_replay.py <session_id> <out_dir> [--speed 8] [--base http://localhost:8001]
Produces <out_dir>/<session_id>.webm (Playwright screen recording) and a few PNG stills.
"""
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("out", type=Path)
    ap.add_argument("--speed", type=float, default=8)
    ap.add_argument("--base", default="http://localhost:8001")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    tmp = a.out / "_raw"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": a.width, "height": a.height},
                                  record_video_dir=str(tmp), record_video_size={"width": a.width, "height": a.height})
        page = ctx.new_page()
        t0 = time.time()
        page.goto(f"{a.base}/?session={a.session}&replay=1&speed={a.speed}")
        while not page.evaluate("window.__replayDone === true") and time.time() - t0 < 900:
            page.wait_for_timeout(1000)
        page.wait_for_timeout(2500)
        page.screenshot(path=str(a.out / "end_of_replay.png"))
        frames = [f for f in page.frames if "view.html" in f.url]
        if frames:  # show interaction after the replay: click a mark in the first view
            box = page.locator("iframe").first.bounding_box()
            target = frames[0].evaluate("""() => { for (const m of document.querySelectorAll('[data-id]')) {
                const b = m.getBoundingClientRect(); if (b.width > 4 && b.height > 4) return {x: b.left + b.width/2, y: b.top + b.height/2}; }
                return null; }""")
            if target:
                page.mouse.move(box["x"] + target["x"], box["y"] + target["y"], steps=15)
                page.wait_for_timeout(1200)
                page.mouse.click(box["x"] + target["x"], box["y"] + target["y"])
                page.wait_for_timeout(2500)
                page.screenshot(path=str(a.out / "after_click.png"))
        video = page.video.path()
        ctx.close()
        browser.close()
    dest = a.out / f"{a.session}.webm"
    shutil.move(video, dest)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"video: {dest} ({dest.stat().st_size / 1e6:.1f} MB), {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
