"""Headless rendering + generic interaction tests for visualization modules (PLAN §3.5, §4.4).

render_viz() loads a module in the same host runtime the web UI uses, inside headless Chromium,
and returns a RenderReport: errors, layout metrics, screenshots and interaction-test results.
Nothing here knows about chart types; every check works on data-bound marks and the module contract.
"""
from __future__ import annotations

import json
import mimetypes
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import numpy as np
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

from ..config import settings
from .cdn import ALLOWED_HOSTS, cached_fetch

STATIC = Path(__file__).parent / "static"
ORIGIN = "http://sciviz.local"

METRICS_JS = r"""
() => {
  const root = document.getElementById('root');
  const R = root.getBoundingClientRect();
  const marks = Array.from(root.querySelectorAll('[data-id],[data-key]'));
  const all = root.querySelectorAll('*').length;
  const canvases = root.querySelectorAll('canvas').length;
  const texts = Array.from(root.querySelectorAll('text, span, div, p, label'))
    .filter(e => e.childElementCount === 0 && (e.textContent || '').trim().length > 0)
    .map(e => e.getBoundingClientRect()).filter(b => b.width > 0 && b.height > 0).slice(0, 600);
  let overlapping = 0;
  for (let i = 0; i < texts.length; i++) {
    for (let j = i + 1; j < texts.length; j++) {
      const a = texts[i], b = texts[j];
      const ix = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
      const iy = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
      if (ix * iy > 0.3 * Math.min(a.width * a.height, b.width * b.height)) { overlapping++; break; }
    }
  }
  let oob = 0;
  for (const m of marks) {
    const b = m.getBoundingClientRect();
    if (b.width === 0 && b.height === 0) continue;
    if (b.right < R.left - 1 || b.left > R.right + 1 || b.bottom < R.top - 1 || b.top > R.bottom + 1) oob++;
  }
  return { marks: marks.length, elements: all, canvases, texts: texts.length,
           text_overlap_ratio: texts.length ? +(overlapping / texts.length).toFixed(3) : 0,
           out_of_bounds_marks: oob, has_pick: !!(window.__sciviz.instance && window.__sciviz.instance.pick),
           has_update: !!(window.__sciviz.instance && window.__sciviz.instance.update),
           has_set_selection: !!(window.__sciviz.instance && window.__sciviz.instance.setSelection),
           has_highlight: !!(window.__sciviz.instance && window.__sciviz.instance.highlight) };
}
"""

TARGETS_JS = r"""
(n) => {
  const root = document.getElementById('root');
  const out = [];
  const marks = Array.from(root.querySelectorAll('[data-id],[data-key]'));
  const step = Math.max(1, Math.floor(marks.length / (n * 3)));
  for (let i = 0; i < marks.length && out.length < n; i += step) {
    const m = marks[i], b = m.getBoundingClientRect();
    if (b.width < 2 || b.height < 2) continue;
    const x = b.left + b.width / 2, y = b.top + b.height / 2;
    const hit = document.elementFromPoint(x, y);
    if (!hit || !(hit === m || m.contains(hit) || (hit.closest && hit.closest('[data-id],[data-key]') === m))) continue;
    const id = m.getAttribute('data-id'), key = m.getAttribute('data-key');
    out.push({ x, y, id, key, type: m.getAttribute('data-type') });
  }
  if (!out.length && window.__sciviz.instance && window.__sciviz.instance.pick) {
    const R = root.getBoundingClientRect();
    for (let gx = 0.1; gx < 1 && out.length < n; gx += 0.08) for (let gy = 0.1; gy < 1 && out.length < n; gy += 0.08) {
      const it = window.__sciviz.instance.pick(R.width * gx, R.height * gy);
      if (it) out.push({ x: R.left + R.width * gx, y: R.top + R.height * gy, id: it.id ?? null,
                         key: it.key !== undefined ? JSON.stringify(it.key) : null, type: it.type });
    }
  }
  return out;
}
"""


@dataclass
class RenderReport:
    ok: bool
    ready: bool
    error: str | None
    errors: list[str]
    blocked_requests: list[str]
    metrics: dict
    blank: bool
    render_seconds: float
    screenshots: dict[str, str]
    interactions: list[dict] = field(default_factory=list)

    @property
    def interaction_failures(self) -> list[dict]:
        return [t for t in self.interactions if not t["passed"]]

    def to_dict(self) -> dict:
        return asdict(self)

    def text(self) -> str:
        lines = [f"render: {'OK' if self.ok else 'FAILED'} in {self.render_seconds:.1f}s"]
        if self.error:
            lines.append(f"fatal error: {self.error[:1500]}")
        for e in self.errors[:8]:
            lines.append(f"console/page error: {e[:500]}")
        for b in self.blocked_requests[:5]:
            lines.append(f"blocked network request (not an allowed CDN): {b}")
        m = self.metrics
        if m:
            lines.append(
                f"metrics: {m.get('marks', 0)} data-bound marks, {m.get('elements', 0)} DOM elements, "
                f"{m.get('canvases', 0)} canvases, text overlap ratio {m.get('text_overlap_ratio')}, "
                f"{m.get('out_of_bounds_marks', 0)} marks outside the view; implements "
                f"update={m.get('has_update')}, setSelection={m.get('has_set_selection')}, "
                f"highlight={m.get('has_highlight')}, pick={m.get('has_pick')}")
        if self.blank:
            lines.append("the rendered view looks blank")
        for t in self.interactions:
            lines.append(f"interaction test {t['name']}: {'pass' if t['passed'] else 'FAIL'} - {t['detail']}")
        return "\n".join(lines)


def _diff_ratio(a: Path, b: Path) -> float:
    ia, ib = Image.open(a).convert("L"), Image.open(b).convert("L")
    if ia.size != ib.size:
        return 1.0
    d = ImageChops.difference(ia, ib).point(lambda v: 255 if v > 16 else 0)
    return float(np.count_nonzero(np.asarray(d))) / (ia.size[0] * ia.size[1])


def _is_blank(p: Path) -> bool:
    return ImageStat.Stat(Image.open(p).convert("L")).stddev[0] < 3


def _alt_value(schema: dict, current: Any) -> Any:
    if "enum" in schema and len(schema["enum"]) > 1:
        return next(v for v in schema["enum"] if v != current)
    t = schema.get("type")
    if t == "boolean":
        return not bool(current)
    if t in ("number", "integer"):
        lo, hi = schema.get("minimum"), schema.get("maximum")
        cur = current if isinstance(current, (int, float)) else schema.get("default", lo if lo is not None else 1)
        if lo is not None and hi is not None:
            alt = lo + (hi - lo) * (0.25 if cur > (lo + hi) / 2 else 0.75)
        else:
            alt = cur * 2 if cur else 1
        return int(round(alt)) if t == "integer" else round(alt, 4)
    return None


def render_viz(module_code: str, data: dict[str, Any], out_dir: Path, *, params: dict | None = None,
               params_schema: dict | None = None, width: int | None = None, height: int | None = None,
               mode: str = "light", run_interactions: bool = True, tag: str = "") -> RenderReport:
    width, height = width or settings.viewport[0], height or settings.viewport[1]
    out_dir.mkdir(parents=True, exist_ok=True)
    params = dict(params or {})
    props = (params_schema or {}).get("properties", {}) if isinstance(params_schema, dict) else {}
    for k, sch in props.items():
        params.setdefault(k, sch.get("default"))
    cfg = {"moduleUrl": f"{ORIGIN}/viz/module.js", "themeUrl": f"{ORIGIN}/runtime/theme.json",
           "dataUrls": {name: f"{ORIGIN}/data/{name}.json" for name in data}, "params": params,
           "width": width, "height": height, "mode": mode, "viewId": "gate"}
    errors: list[str] = []
    blocked: list[str] = []
    data_blobs = {name: json.dumps(v, default=str).encode() for name, v in data.items()}
    data_text = b"\n".join(data_blobs.values()).decode("utf8", "ignore")

    def handle(route, request):
        url = request.url
        if url.startswith(ORIGIN):
            path = urlsplit(url).path
            if path == "/viz/module.js":
                return route.fulfill(status=200, content_type="application/javascript", body=module_code)
            if path.startswith("/data/"):
                name = path[len("/data/"):].removesuffix(".json")
                if name in data_blobs:
                    return route.fulfill(status=200, content_type="application/json", body=data_blobs[name])
            if path.startswith("/runtime/"):
                f = STATIC / path[len("/runtime/"):]
                if f.is_file():
                    ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
                    if f.suffix == ".js":
                        ctype = "application/javascript"
                    return route.fulfill(status=200, content_type=ctype, body=f.read_bytes())
            return route.fulfill(status=404, body=b"not found")
        host = urlsplit(url).hostname
        if host in ALLOWED_HOSTS:
            try:
                status, ctype, body = cached_fetch(url)
            except Exception as e:  # network trouble -> surfaced as a module load error
                errors.append(f"CDN fetch failed for {url}: {e}")
                return route.abort()
            return route.fulfill(status=status, content_type=ctype, body=body,
                                 headers={"Access-Control-Allow-Origin": "*"})
        blocked.append(url)
        return route.abort()

    shots: dict[str, str] = {}
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width + 40, "height": height + 40}, device_scale_factor=1)
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route("**/*", handle)
        page.add_init_script(f"window.__SCIVIZ_CONFIG__ = {json.dumps(cfg)};")
        page.goto(f"{ORIGIN}/runtime/host.html")
        ready = error = None
        try:
            page.wait_for_function("window.__sciviz && (window.__sciviz.ready || window.__sciviz.error)", timeout=45000)
            ready = page.evaluate("window.__sciviz.ready")
            error = page.evaluate("window.__sciviz.error")
        except Exception as e:
            error = f"timed out waiting for the view to render: {e}"
        errors += page.evaluate("window.__sciviz ? window.__sciviz.errors : []") or []
        metrics = page.evaluate(METRICS_JS) if ready else {}
        root = page.locator("#root")
        base = out_dir / f"{tag}default.png"
        root.screenshot(path=str(base))
        shots["default"] = str(base)
        render_seconds = time.time() - t0
        blank = _is_blank(base)
        tests: list[dict] = []

        if ready and run_interactions:
            targets = page.evaluate(TARGETS_JS, 3)
            if not targets:
                tests.append({"name": "data_bound_marks", "passed": False,
                              "detail": "no clickable data-bound marks found (tag marks with data-id/data-type or "
                                        "data-key, or implement pick(x, y) for canvas rendering)"})
            else:
                t = targets[0]
                expected = t["id"] if t["id"] is not None else t["key"]
                # hover -> details event
                page.mouse.move(t["x"], t["y"])
                page.wait_for_timeout(200)
                hovers = [e for e in page.evaluate("window.__sciviz.log") if e["type"] == "hover" and e["payload"]["item"]]
                tests.append({"name": "hover_details", "passed": bool(hovers),
                              "detail": f"hovering a mark emitted {len(hovers)} hover event(s)"})
                page.mouse.move(2, 2)
                page.evaluate("window.__sciviz.setSelection([])")
                page.wait_for_timeout(300)
                clean = out_dir / f"{tag}clean.png"
                root.screenshot(path=str(clean))
                # click -> selection event with an id that exists in the data
                page.mouse.click(t["x"], t["y"])
                page.wait_for_timeout(400)
                sel = page.evaluate("window.__sciviz.selection")
                ids = [str(s.get("id")) for s in sel if s.get("id") is not None]
                keys = [s.get("key") for s in sel if s.get("key") is not None]
                in_data = any(f'"{i}"' in data_text or i in data_text for i in ids) or bool(keys and all(
                    all(f'"{k}"' in data_text for k in (kk.keys() if isinstance(kk, dict) else [])) for kk in keys))
                tests.append({"name": "click_select", "passed": bool(sel) and in_data,
                              "detail": f"click selected {sel[:2]}; ids/keys found in bound data: {in_data}"})
                selected = out_dir / f"{tag}selected.png"
                root.screenshot(path=str(selected))
                shots["selected"] = str(selected)
                r = _diff_ratio(clean, selected)
                tests.append({"name": "selection_visible", "passed": r > 0.0005,
                              "detail": f"{r * 100:.2f}% of pixels changed after selecting"})
                page.evaluate("window.__sciviz.setSelection([])")
                page.wait_for_timeout(250)
                item = {"type": t["type"] or "item"}
                if t["id"] is not None:
                    item["id"] = t["id"]
                else:
                    item["key"] = json.loads(t["key"]) if t["key"] else None
                page.evaluate("(it) => window.__sciviz.highlight([it])", item)
                page.wait_for_timeout(350)
                hl = out_dir / f"{tag}highlight.png"
                root.screenshot(path=str(hl))
                r = _diff_ratio(clean, hl)
                tests.append({"name": "highlight_visible", "passed": r > 0.0005,
                              "detail": f"{r * 100:.2f}% of pixels changed after highlight([{expected}])"})
                page.evaluate("window.__sciviz.highlight([])")
                page.wait_for_timeout(250)
            # parameters -> update without errors and with a visible change
            for name, sch in list(props.items())[:4]:
                alt = _alt_value(sch, params.get(name))
                if alt is None:
                    continue
                n_err = len(errors) + len(page.evaluate("window.__sciviz.errors"))
                before = out_dir / f"{tag}param_{name}_before.png"
                root.screenshot(path=str(before))
                try:
                    page.evaluate("(p) => window.__sciviz.setParams(p)", {name: alt})
                    page.wait_for_timeout(900)
                    ok_run = True
                except Exception as e:
                    ok_run, errors = False, errors + [f"setParams({name}) failed: {e}"]
                after = out_dir / f"{tag}param_{name}.png"
                root.screenshot(path=str(after))
                changed = _diff_ratio(before, after)
                new_err = len(errors) + len(page.evaluate("window.__sciviz.errors")) - n_err
                tests.append({"name": f"param_{name}", "passed": ok_run and new_err == 0 and changed > 0.0005,
                              "detail": f"set {name}={alt!r}: {new_err} new errors, {changed * 100:.2f}% pixels changed"})
                try:
                    page.evaluate("(p) => window.__sciviz.setParams(p)", {name: params.get(name)})
                    page.wait_for_timeout(500)
                except Exception:
                    pass
            errors = list(dict.fromkeys(errors + (page.evaluate("window.__sciviz.errors") or [])))
        browser.close()

    ok = bool(ready) and not error and not errors and not blank
    return RenderReport(ok=ok, ready=bool(ready), error=error, errors=errors, blocked_requests=blocked,
                        metrics=metrics, blank=blank, render_seconds=round(render_seconds, 2),
                        screenshots=shots, interactions=tests)
