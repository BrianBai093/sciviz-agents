"""UI smoke test against a running dev stack (API on :8000, Vite on :5173). Not part of the unit tests.

Checks with a recorded session (no LLM calls):
  1. the views render inside their sandboxed iframes;
  2. clicking a data mark in one view selects it, shows the selection chip in the chat, and the
     same item is selected in the other (linked) view;
  3. changing a parameter control re-renders the view.
Run: uv run python tests/ui/ui_smoke.py <session_id> [out_dir]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

UI = "http://localhost:5173"


def view_frames(page):
    return [f for f in page.frames if "view.html" in f.url]


def main(session: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1680, "height": 960})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{UI}/?session={session}")
        deadline = time.time() + 40
        while time.time() < deadline:
            frames = view_frames(page)
            ready = [f.evaluate("window.__sciviz && window.__sciviz.ready") if f else False for f in frames]
            if frames and all(ready):
                break
            page.wait_for_timeout(500)
        frames = view_frames(page)
        print(f"view frames: {len(frames)}; ready: {[f.evaluate('window.__sciviz.ready') for f in frames]}")
        print("frame errors:", [f.evaluate("window.__sciviz.errors") for f in frames])
        page.screenshot(path=str(out / "1_loaded.png"))

        # click the first visible data mark in the first view
        f0 = frames[0]
        target = f0.evaluate("""() => {
            const ms = Array.from(document.querySelectorAll('[data-id]'));
            for (const m of ms) { const b = m.getBoundingClientRect();
              if (b.width > 3 && b.height > 3) return {x: b.left + b.width/2, y: b.top + b.height/2,
                id: m.getAttribute('data-id'), label: m.getAttribute('data-label')}; }
            return null; }""")
        print("clicking", target)
        if target:
            frame_el = page.locator("iframe").nth(0).bounding_box()
            page.mouse.click(frame_el["x"] + target["x"], frame_el["y"] + target["y"])
            page.wait_for_timeout(1200)
            chip = page.locator("text=selected").first.inner_text() if page.locator("text=selected").count() else ""
            print("chat chip:", chip)
            for i, f in enumerate(frames):
                print(f"view {i} selection:", f.evaluate("window.__sciviz.selection.map(s => s.id || JSON.stringify(s.key))"))
            page.screenshot(path=str(out / "2_selected.png"))

        # change the first parameter control (range or select) of the second view
        controls = page.locator("section").nth(min(1, len(frames) - 1)).locator("select, input[type=range]")
        if controls.count():
            c = controls.first
            tag = c.evaluate("e => e.tagName")
            if tag == "SELECT":
                opts = c.locator("option").all_inner_texts()
                c.select_option(index=1 if len(opts) > 1 else 0)
            else:
                c.evaluate("e => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;"
                           " s.call(e, String(Math.round((+e.min + +e.max) / 2))); e.dispatchEvent(new Event('input', {bubbles: true})); }")
            page.wait_for_timeout(1500)
            f = view_frames(page)[min(1, len(frames) - 1)]
            print("params after change:", f.evaluate("window.__sciviz.params"))
            page.screenshot(path=str(out / "3_param.png"))
        print("page errors:", errors)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/sciviz_ui"))
