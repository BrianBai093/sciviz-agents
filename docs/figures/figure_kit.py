"""Shared drawing kit for the paper-style figures in docs/figures.

Each figure is an SVG written by a Python script (the source of truth). `render` uses Playwright's Chromium to turn it
into a vector PDF (fonts embedded) and a 300 dpi PNG. Colors follow the app: the agent roles and the accent used for
user input.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

INK, BODY, MUTED, LINE, SURFACE = "#1f2328", "#3a3936", "#5c5b57", "#cfcec8", "#f7f7f5"
ACCENT, ACCENT_DARK, ACCENT_TINT = "#2a78d6", "#1d5fae", "#e8f1fb"  # the app's accent: user input and selection
ROLE = {  # stroke, tint: the agent colors used in the app
    "lead": ("#7c4dcc", "#f3eefb"),
    "data": ("#0f8fa8", "#e7f4f7"),
    "analyst": ("#2e8b43", "#eaf4ec"),
    "viz": ("#c27a00", "#fbf3e3"),
    "critic": ("#c4382b", "#fcebe9"),
}
GREEN_DARK = "#23683a"
FIELDS = ["#eb6834", "#1baf7a", "#eda100"]  # categorical colors for research fields in the mock views
ARROWS = {"grey": "#6b6a66", "blue": ACCENT, "red": ROLE["critic"][0], "green": ROLE["analyst"][0],
          "amber": ROLE["viz"][0]}

STYLE = f"""
text {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; fill: {INK}; }}
.panel {{ font-size: 16px; font-weight: 700; }}
.badge {{ font-size: 11px; font-weight: 700; fill: #fff; }}
.box {{ font-size: 13.5px; font-weight: 700; }}
.box-s {{ font-size: 12px; font-weight: 700; }}
.body {{ font-size: 12px; fill: {BODY}; }}
.small {{ font-size: 11px; fill: {MUTED}; }}
.small-b {{ font-size: 11px; font-weight: 700; }}
.note {{ font-size: 11px; fill: {MUTED}; font-style: italic; }}
.quote {{ font-size: 11.5px; fill: {BODY}; font-style: italic; }}
.mono {{ font-family: Menlo, 'SF Mono', Consolas, 'DejaVu Sans Mono', monospace; font-size: 10.5px;
         font-style: normal; fill: {BODY}; }}
.tiny {{ font-size: 8px; font-weight: 700; fill: #fff; }}
"""

# 24x24 line icons, colored with currentColor
SYMBOLS = """
<symbol id="i-robot" viewBox="0 0 24 24">
  <line x1="12" y1="2.6" x2="12" y2="5.6" stroke="currentColor" stroke-width="1.6"/>
  <circle cx="12" cy="2.3" r="1.5" fill="currentColor"/>
  <rect x="3.6" y="5.6" width="16.8" height="13.6" rx="4" fill="#fff" stroke="currentColor" stroke-width="1.8"/>
  <circle cx="9" cy="11.6" r="1.7" fill="currentColor"/><circle cx="15" cy="11.6" r="1.7" fill="currentColor"/>
  <path d="M9.3 15.4 H14.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
  <rect x="1.2" y="10" width="2.4" height="4.6" rx="1" fill="currentColor"/>
  <rect x="20.4" y="10" width="2.4" height="4.6" rx="1" fill="currentColor"/>
</symbol>
<symbol id="i-user" viewBox="0 0 24 24">
  <circle cx="12" cy="7.5" r="4.3" fill="currentColor"/>
  <path d="M3.5 21.5 C3.5 15.6 7.4 13.1 12 13.1 C16.6 13.1 20.5 15.6 20.5 21.5 Z" fill="currentColor"/>
</symbol>
<symbol id="i-db" viewBox="0 0 24 24">
  <path d="M4 5.5 V18.5 C4 20.4 7.6 22 12 22 C16.4 22 20 20.4 20 18.5 V5.5" fill="#fff" stroke="currentColor" stroke-width="1.5"/>
  <ellipse cx="12" cy="5.5" rx="8" ry="3.2" fill="#fff" stroke="currentColor" stroke-width="1.5"/>
  <path d="M4 12 C4 13.9 7.6 15.4 12 15.4 C16.4 15.4 20 13.9 20 12" fill="none" stroke="currentColor" stroke-width="1.3"/>
</symbol>
<symbol id="i-shield" viewBox="0 0 24 24">
  <path d="M12 2 L20 5.2 V11.2 C20 16.2 16.6 19.8 12 22 C7.4 19.8 4 16.2 4 11.2 V5.2 Z" fill="#fff" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
  <path d="M8.3 12 L11 14.7 L16 9.3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</symbol>
<symbol id="i-check" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="10" fill="currentColor"/>
  <path d="M7.5 12.3 L10.6 15.3 L16.6 8.9" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
</symbol>
<symbol id="i-cursor" viewBox="0 0 24 24">
  <path d="M5 2.5 L5 19.5 L9.3 15.4 L12.2 21.6 L15 20.3 L12.1 14.3 L18 14.3 Z" fill="#fff" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
</symbol>
<symbol id="i-term" viewBox="0 0 24 24">
  <rect x="2.5" y="4" width="19" height="16" rx="2.5" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <path d="M6.5 9.5 L9.5 12 L6.5 14.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M11.5 15 H16.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
</symbol>
<symbol id="i-pkg" viewBox="0 0 24 24">
  <path d="M12 2.5 L20.5 7 V17 L12 21.5 L3.5 17 V7 Z" fill="#fff" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
  <path d="M3.5 7 L12 11.5 L20.5 7 M12 11.5 V21.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
</symbol>
<symbol id="i-log" viewBox="0 0 24 24">
  <rect x="4" y="2.5" width="16" height="19" rx="2" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <path d="M8 8 H16 M8 12 H16 M8 16 H12.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
</symbol>
<symbol id="i-retry" viewBox="0 0 24 24">
  <path d="M19.5 12 A7.5 7.5 0 1 1 16.9 6.3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <path d="M17.6 2.6 V7 H13.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</symbol>
<symbol id="i-coin" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="9" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <path d="M14.8 8.6 C14.2 7.7 13.2 7.3 12 7.3 C10.3 7.3 9.2 8.2 9.2 9.5 C9.2 12.3 15 11.2 15 14.3 C15 15.7 13.8 16.7 12 16.7 C10.7 16.7 9.6 16.2 9 15.2 M12 5.6 V7.3 M12 16.7 V18.4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
</symbol>
<symbol id="i-layers" viewBox="0 0 24 24">
  <path d="M12 3 L21 8 L12 13 L3 8 Z" fill="#fff" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
  <path d="M3 12 L12 17 L21 12 M3 16 L12 21 L21 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
</symbol>
<symbol id="i-table" viewBox="0 0 24 24">
  <rect x="3" y="4" width="18" height="16" rx="1.5" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <path d="M3 9 H21 M3 14.5 H21 M9.5 4 V20" stroke="currentColor" stroke-width="1.3"/>
</symbol>
<symbol id="i-graph" viewBox="0 0 24 24">
  <path d="M6 6 L17 8 L8 18 Z M17 8 L19 18 L8 18" fill="none" stroke="currentColor" stroke-width="1.4"/>
  <circle cx="6" cy="6" r="2.6" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <circle cx="17" cy="8" r="2.6" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <circle cx="8" cy="18" r="2.6" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <circle cx="19" cy="18" r="2.6" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
</symbol>
<symbol id="i-doc" viewBox="0 0 24 24">
  <path d="M6 2.5 H14.5 L19 7 V21.5 H6 Z" fill="#fff" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
  <path d="M14.5 2.5 V7 H19" fill="none" stroke="currentColor" stroke-width="1.4"/>
  <path d="M9 12 H16 M9 15.5 H16 M9 19 H13" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
</symbol>
<symbol id="i-code" viewBox="0 0 24 24">
  <rect x="2.5" y="4" width="19" height="16" rx="2" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <path d="M9 9 L6 12 L9 15 M15 9 L18 12 L15 15 M13 8.5 L11 15.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</symbol>
"""

# icons used only by later figures (kept out of SYMBOLS so earlier figures stay unchanged)
EXTRA_SYMBOLS = """
<symbol id="i-globe" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="9" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <path d="M3 12 H21 M12 3 C8.6 6.4 8.6 17.6 12 21 M12 3 C15.4 6.4 15.4 17.6 12 21" fill="none" stroke="currentColor" stroke-width="1.3"/>
</symbol>
<symbol id="i-clock" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="9" fill="#fff" stroke="currentColor" stroke-width="1.6"/>
  <path d="M12 6.8 V12 L15.6 14.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
</symbol>
"""

out: list[str] = []


def add(s: str) -> None:
    out.append(s)


def rect(x, y, w, h, *, rx=6, fill="#fff", stroke=LINE, sw=1.0, dash=None) -> None:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"{d}/>')


def text(x, y, s, cls="body", anchor="start", fill=None, raw=False) -> None:
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f = f' style="fill:{fill}"' if fill else ""
    add(f'<text x="{x}" y="{y}" class="{cls}"{a}{f}>{s if raw else escape(s)}</text>')


def lines(x, y, items, lh=13.0, cls="body", anchor="start", fill=None) -> None:
    for i, item in enumerate(items):
        s, c = item if isinstance(item, tuple) else (item, cls)
        text(x, y + i * lh, s, c, anchor, fill)


def icon(name, x, y, size, color) -> None:
    add(f'<use href="#i-{name}" x="{x}" y="{y}" width="{size}" height="{size}" style="color:{color}"/>')


def arrow(d, color="grey", sw=1.2, dash=None, start=False, end=True, small=False) -> None:
    m = f"a-{color}{'-s' if small else ''}"
    marks = (f' marker-end="url(#{m})"' if end else "") + (f' marker-start="url(#{m})"' if start else "")
    da = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<path d="{d}" fill="none" stroke="{ARROWS[color]}" stroke-width="{sw}"{da}{marks} '
        f'stroke-linecap="round" stroke-linejoin="round"/>')


def markers() -> str:
    s = []
    for k, c in ARROWS.items():
        for suffix, size in (("", 7), ("-s", 5)):
            s.append(f'<marker id="a-{k}{suffix}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="{size}" '
                     f'markerHeight="{size}" markerUnits="userSpaceOnUse" orient="auto-start-reverse">'
                     f'<path d="M0,1 L10,5 L0,9 Z" fill="{c}"/></marker>')
    return "".join(s)


def panel(x, y, w, h, num, title) -> None:
    rect(x, y, w, h, rx=10, fill=SURFACE, stroke="#dcdbd5")
    add(f'<circle cx="{x + 17}" cy="{y + 19}" r="9" fill="{INK}"/>')
    text(x + 17, y + 22.8, str(num), "badge", "middle")
    text(x + 32, y + 24.5, title, "panel")



def svg_document(width: int, height: int, width_in: float, extra_defs: str = "") -> str:
    """The SVG for everything drawn with `add` so far, `width` x `height` drawing units, printed `width_in` wide."""
    height_in = round(width_in * height / width, 3)
    defs = f"<defs><style>{STYLE}</style>{SYMBOLS}{markers()}{extra_defs}</defs>"
    body = "\n".join(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width_in}in" '
            f'height="{height_in}in">\n{defs}\n<rect width="{width}" height="{height}" fill="#fff"/>\n{body}\n</svg>\n')


def render(svg: str, folder: Path, name: str, width_in: float, height_in: float) -> None:
    """Write <name>.pdf (vector) and <name>.png (300 dpi) from the SVG."""
    from playwright.sync_api import sync_playwright

    html = ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;padding:0}"
            f"svg{{display:block;width:{width_in}in;height:{height_in}in}}</style></head><body>{svg}</body></html>")
    px_w, px_h = round(width_in * 96), round(height_in * 96)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": px_w, "height": px_h}, device_scale_factor=300 / 96)
        page.set_content(html)
        page.pdf(path=str(folder / f"{name}.pdf"), width=f"{width_in}in", height=f"{height_in}in",
                 print_background=True, page_ranges="1")
        page.screenshot(path=str(folder / f"{name}.png"), clip={"x": 0, "y": 0, "width": px_w, "height": px_h})
        browser.close()
