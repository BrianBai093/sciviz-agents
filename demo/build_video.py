"""Build the narrated demo video from a storyboard (replay mode: no LLM calls for the agents, TTS only).

  uv run python demo/build_video.py demo/storyboard.yaml --out demo/video/sciviz_demo.mp4

Each storyboard step has narration (`say`) and UI actions (`do`). Narration is synthesized with OpenAI TTS
(cached in demo/tts_cache/), the UI is driven by Playwright in "director" mode (recorded events applied at a
scripted pace), captions are overlaid in the page, and ffmpeg places every audio clip at its step's start time.
Requires the API server with the built UI (e.g. `sciviz serve --port 8001`, no API key needed for the UI).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

import yaml
from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).resolve().parent
CACHE = HERE / "tts_cache"
VOICE, TTS_MODEL = "marin", "gpt-4o-mini-tts"
STYLE = "Calm, clear and friendly; a researcher presenting a software demo; natural pace."

CAPTION_JS = """(text) => {
  let el = document.getElementById('__caption');
  if (!el) {
    el = document.createElement('div'); el.id = '__caption';
    Object.assign(el.style, {position: 'fixed', left: '50%', bottom: '18px', transform: 'translateX(-50%)',
      maxWidth: '1100px', padding: '8px 16px', background: 'rgba(20,20,20,0.78)', color: '#fff', zIndex: 99999,
      font: '500 17px/1.45 Inter, system-ui, sans-serif', borderRadius: '8px', textAlign: 'center',
      pointerEvents: 'none'});
    document.body.appendChild(el);
  }
  el.textContent = text; el.style.display = text ? 'block' : 'none';
}"""


def tts(text: str) -> tuple[Path, float]:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / (hashlib.sha1(f"{VOICE}|{TTS_MODEL}|{STYLE}|{text}".encode()).hexdigest()[:16] + ".mp3")
    if not path.exists():
        from openai import OpenAI
        with OpenAI().audio.speech.with_streaming_response.create(
                model=TTS_MODEL, voice=VOICE, input=text, instructions=STYLE, response_format="mp3") as r:
            r.stream_to_file(path)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "default=nw=1:nk=1", str(path)]).decode().strip())
    return path, dur


class Director:
    def __init__(self, page: Page, base: str):
        self.page, self.base = page, base

    def caption(self, text: str) -> None:
        self.page.evaluate(CAPTION_JS, text)

    def open(self, session: str, drawer: str | None = None) -> None:
        self.page.goto(f"{self.base}/?session={session}&director=1")
        self.page.wait_for_function("window.__director && window.__director.loaded", timeout=60000)
        if drawer:
            self.drawer(drawer)

    def slide(self, path: str) -> None:
        self.page.goto((HERE / path).resolve().as_uri())

    def drawer(self, name: str) -> None:
        self.page.get_by_role("button", name=name.capitalize(), exact=True).click()

    def _find(self, until) -> int:
        evs = self.page.evaluate("window.__director.events()")
        if until == "end":
            return len(evs)
        nth, hits = until.get("nth", 1), 0
        start = self.page.evaluate("window.__director.index()")
        for e in evs[start:]:
            p = e["payload"] or {}
            if e["kind"] != until["kind"]:
                continue
            if "agent" in until and e["agent"] != until["agent"]:
                continue
            if any(str(p.get(k)) != str(v) for k, v in (until.get("payload") or {}).items()):
                continue
            hits += 1
            if hits == nth:
                return e["i"] + 1
        raise RuntimeError(f"no event matches {until} after index {start}")

    def play(self, until, ms: int) -> None:
        target = self._find(until)
        self.page.evaluate("([t, ms]) => window.__director.playTo(t, ms)", [target, ms])

    def type(self, text: str, delay: int = 22) -> None:
        box = self.page.locator("textarea")
        box.click()
        box.type(text, delay=delay)
        self.page.wait_for_timeout(500)
        box.press("Enter")

    def type_next(self, delay: int = 12) -> None:
        """Type the next recorded user message exactly as it was sent (it then appears when played)."""
        evs = self.page.evaluate("window.__director.events()")
        start = self.page.evaluate("window.__director.index()")
        text = next(e["payload"]["text"] for e in evs[start:]
                    if e["kind"] == "message" and e["agent"] == "user" and not e["payload"].get("answer_to"))
        self.type(text, delay)

    def _frame(self, view: int):
        frames = [f for f in self.page.frames if "view.html" in f.url]
        return frames[view], self.page.locator("iframe").nth(view)

    def _mark_point(self, view: int, mark_id: str | None):
        frame, el = self._frame(view)
        pt = frame.evaluate("""(id) => {
            const ms = id ? [document.querySelector(`[data-id="${id}"]`)] : Array.from(document.querySelectorAll('[data-id],[data-key]'));
            for (const m of ms) { if (!m) continue; const b = m.getBoundingClientRect();
              if (b.width > 3 && b.height > 3) return {x: b.left + b.width / 2, y: b.top + b.height / 2}; }
            return null; }""", mark_id)
        box = el.bounding_box()
        if not pt or not box:
            return None
        # the iframe may be scaled to fit its panel (D39)
        scale = box["width"] / max(frame.evaluate("window.innerWidth"), 1)
        return box["x"] + pt["x"] * scale, box["y"] + pt["y"] * scale

    def hover(self, view: int = 0, id: str | None = None) -> None:
        pt = self._mark_point(view, id)
        if pt:
            self.page.mouse.move(*pt, steps=20)

    def click(self, view: int = 0, id: str | None = None) -> None:
        pt = self._mark_point(view, id)
        if pt:
            self.page.mouse.move(*pt, steps=20)
            self.page.wait_for_timeout(300)
            self.page.mouse.click(*pt)

    def wait(self, ms: int) -> None:
        self.page.wait_for_timeout(ms)

    def button(self, name: str) -> None:
        self.page.get_by_role("button", name=name).first.click()

    def param(self, panel: int = 0, index: int = 0) -> None:
        """Change one generated parameter control of a view panel (next option / middle of a slider)."""
        ctl = self.page.locator("section").nth(panel).locator("select, input[type=range]").nth(index)
        if ctl.evaluate("e => e.tagName") == "SELECT":
            n = ctl.locator("option").count()
            cur = ctl.evaluate("e => e.selectedIndex")
            ctl.select_option(index=(cur + 1) % max(n, 1))
        else:
            ctl.evaluate("e => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;"
                         " s.call(e, String(Math.round(+e.min + (+e.max - +e.min) * 0.6)));"
                         " e.dispatchEvent(new Event('input', {bubbles: true})); }")


def run(storyboard: Path, out: Path, base: str, size: tuple[int, int]) -> None:
    sb = yaml.safe_load(storyboard.read_text())
    steps = sb["steps"]
    clips = [tts(s["say"]) if s.get("say") else (None, 0.0) for s in steps]
    print(f"narration: {sum(d for _, d in clips):.0f}s in {len(steps)} steps")
    raw = out.parent / "_raw"
    shutil.rmtree(raw, ignore_errors=True)
    placed: list[tuple[float, Path]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": size[0], "height": size[1]}, record_video_dir=str(raw),
                                  record_video_size={"width": size[0], "height": size[1]})
        page = ctx.new_page()
        t0 = time.time()
        d = Director(page, base)
        for step, (clip, dur) in zip(steps, clips):
            start = time.time() - t0
            if step.get("say") and not step.get("say_after_do"):
                d.caption(step.get("caption", step["say"]))
                placed.append((start, clip))
            for action in step.get("do", []):
                (name, arg), = action.items() if isinstance(action, dict) else ((action, None),)
                fn = getattr(d, name)
                if isinstance(arg, dict):
                    fn(**arg)
                elif arg is None:
                    fn()
                else:
                    fn(arg)
            if step.get("say") and step.get("say_after_do"):
                d.caption(step.get("caption", step["say"]))
                placed.append((time.time() - t0, clip))
            elapsed = time.time() - t0 - (placed[-1][0] if step.get("say") else start)
            page.wait_for_timeout(int(max(0.0, dur + step.get("pad", 0.4) - elapsed) * 1000))
            print(f"{start:6.1f}s  {step.get('say', '')[:70]}", flush=True)
        d.caption("")
        page.wait_for_timeout(800)
        video = Path(page.video.path())
        ctx.close()
        browser.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs, filters = ["-i", str(video)], []
    for k, (at, clip) in enumerate(placed, start=1):
        inputs += ["-i", str(clip)]
        ms = int(at * 1000)
        filters.append(f"[{k}:a]adelay={ms}|{ms}[a{k}]")
    mix = "".join(f"[a{k}]" for k in range(1, len(placed) + 1))
    filters.append(f"{mix}amix=inputs={len(placed)}:normalize=0[aout]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "0:v", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", str(out)], check=True)
    shutil.rmtree(raw, ignore_errors=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                         "default=nw=1:nk=1", str(out)]).decode())
    (out.with_suffix(".timeline.json")).write_text(json.dumps([{"at": round(a, 2), "clip": c.name} for a, c in placed], indent=1))
    print(f"video: {out} ({dur:.0f}s, {out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard", type=Path)
    ap.add_argument("--out", type=Path, default=HERE / "video" / "sciviz_demo.mp4")
    ap.add_argument("--base", default="http://localhost:8001")
    ap.add_argument("--size", default="1600x900")
    a = ap.parse_args()
    w, h = (int(x) for x in a.size.split("x"))
    run(a.storyboard, a.out, a.base, (w, h))
