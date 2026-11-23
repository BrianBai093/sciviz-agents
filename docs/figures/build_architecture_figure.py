"""Build the sciviz architecture figure (Design Test, Option A): a paper-style overview of the system.

    uv run python docs/figures/build_architecture_figure.py

The drawing code below writes the SVG (the source of truth). Playwright's Chromium then renders a vector PDF
(7 in wide, the width of a two-column paper figure, fonts embedded) and a 300 dpi PNG next to it.
Layout: (1) input -> (2) multi-agent harness -> (3) interactive web app, a user feedback loop from (3) back to
(2), and the shared harness services along the bottom.
"""
from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
NAME = "sciviz_architecture"
W, H = 1000, 460  # drawing units
WIDTH_IN = 7.0  # printed width
HEIGHT_IN = round(WIDTH_IN * H / W, 3)

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


# ---------------------------------------------------------------------------------------------------------------
# (1) Input
def draw_input() -> None:
    panel(10, 10, 146, 324, 1, "Input")
    icon("user", 18, 40, 20, MUTED)
    text(43, 55, "User", "box-s")
    rect(18, 66, 130, 48, rx=6, fill="#fff", stroke=LINE)
    add(f'<path d="M26,66.6 L29,59.5 L35,66.6" fill="#fff" stroke="{LINE}" stroke-width="1" stroke-linejoin="round"/>')
    lines(26, 82, ["“How do our top 80", "researchers", "collaborate?”"], lh=13, cls="quote")
    rect(18, 121, 130, 18, rx=9, fill=ACCENT_TINT, stroke=ACCENT, sw=0.8)
    icon("cursor", 24, 123.5, 13, ACCENT)
    text(40, 133.8, "+ current selection", "small", fill=ACCENT_DARK)

    icon("db", 61, 176, 44, ROLE["data"][0])
    text(83, 238, "OpenAlex snapshot", "box-s", "middle")
    lines(83, 252, ["Columbia University", "2021–24 · 55k works"], lh=13, cls="small", anchor="middle")
    text(83, 280, "DuckDB + catalog", "mono", "middle")
    text(83, 304, "datasets are pluggable", "note", "middle")


# ---------------------------------------------------------------------------------------------------------------
# (2) Multi-agent harness
def draw_harness() -> None:
    panel(166, 10, 530, 324, 2, "Multi-agent harness")
    rect(446, 18, 240, 18, rx=9, fill="#e9f5ec", stroke=ROLE["analyst"][0], sw=0.8)
    icon("check", 451, 20.5, 13, ROLE["analyst"][0])
    text(469, 30.8, "no technique-specific prompts or code", "small", fill=GREEN_DARK)

    # Lead
    s, t = ROLE["lead"]
    rect(230, 46, 224, 70, rx=8, fill=t, stroke=s, sw=1.3)
    icon("robot", 240, 55, 26, s)
    text(274, 66, "Lead agent", "box")
    lines(274, 80, ["plans · delegates · answers", "every claim cites an artifact"], lh=14)
    text(274, 108, "task(brief) · show_view", "mono")

    # Lead <-> specialists
    for x1, x2 in ((262, 228), (342, 342), (422, 456)):
        arrow(f"M{x1},118 L{x2},144", "grey", 1.1, start=True, small=True)
    text(336, 135, "brief / report", "note", "end")

    # specialists
    spec = [
        ("data", 176, "Data", ["catalog lookup,", "read-only SQL", "→ clean tables", ("run_sql", "mono")]),
        ("analyst", 290, "Analyst", ["Python kernel:", "stats, graphs,", "trees, layouts", ("run_python", "mono")]),
        ("viz", 404, "Viz", ["picks technique,", "finds npm libs,", ("module.js", "mono"), ("viz.json", "mono")]),
    ]
    for role, x, title, body in spec:
        s, t = ROLE[role]
        rect(x, 146, 104, 90, rx=8, fill=t, stroke=s, sw=1.3)
        icon("robot", x + 8, 152, 20, s)
        text(x + 33, 167, title, "box")
        lines(x + 10, 186, body, lh=13)

    # artifact store
    rect(176, 248, 332, 40, rx=8, fill="#fff", stroke=LINE)
    for i, n in enumerate(("table", "graph", "doc", "code")):
        icon(n, 184 + i * 22, 258, 20, MUTED)
    text(280, 264, "Shared artifact store", "box-s")
    text(280, 279, "each with lineage and producing code", "small")
    for x in (228, 342, 456):
        arrow(f"M{x},238 V246", "grey", 1, start=True, small=True)

    # Viz <-> gate revision loop
    arrow("M509,174 H554", "amber", 1.3)
    text(531.5, 168, "submit", "note", "middle")
    arrow("M555,208 H511", "red", 1.3, dash="3 2")
    text(533, 221, "revise", "note", "middle", fill=ROLE["critic"][0])
    icon("retry", 515, 183, 16, ROLE["critic"][0])
    text(534, 195.5, "×N", "small-b", fill=ROLE["critic"][0])

    # verification gate
    s, t = ROLE["critic"]
    rect(556, 130, 130, 182, rx=8, fill=t, stroke=s, sw=1.3)
    icon("shield", 564, 138, 22, s)
    lines(592, 150, ["Verification", "gate"], lh=14, cls="box")
    text(564, 184, "enforced by the harness", "note")
    steps = [(202, ["static checks,", "pinned imports"]), (231, ["headless render"]),
             (247, ["interaction tests:", "hover · select ·", "highlight · params"])]
    for i, (y, ls) in enumerate(steps, 1):
        add(f'<circle cx="569" cy="{y - 3.7}" r="5" fill="{s}"/>')
        text(569, y - 1, str(i), "tiny", "middle")
        lines(579, y, ls, lh=13, cls="small")
    rect(562, 280, 118, 26, rx=5, fill="#fff", stroke=s, sw=0.9)
    icon("robot", 566, 283, 20, s)
    text(590, 291, "Critic agent", "box-s")
    text(590, 302, "vision → verdict", "small")

    # approved views leave through the Lead's answer (the arrow into the app is drawn with the other flows)
    arrow("M630,129 V75", "green", 1.4)
    text(636, 106, "approved", "small-b", fill="#2e7d32")

    # follow-ups: the Lead picks the cheapest path
    rect(176, 294, 332, 34, rx=8, fill="#fff", stroke=LINE)
    text(184, 315, "Lead picks:", "small-b")
    paths = [("parameters", "≈15 s", "lead"), ("highlight", "≈10 s", "lead"),
             ("code edit", "≈4 min (+gate)", "viz")]
    for i, (a, b, role) in enumerate(paths):
        x = 254 + i * 86
        s, t = ROLE[role]
        rect(x, 297, 82, 28, rx=9, fill=t, stroke=s, sw=0.9)
        text(x + 41, 309, a, "small-b", "middle")
        text(x + 41, 320.5, b, "small", "middle")


# ---------------------------------------------------------------------------------------------------------------
# (3) Interactive web app
def node_xy(cx, cy, r, k, n=18):
    a = math.radians(-90 + k * 360 / n)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def draw_force_view() -> None:
    nodes = {"o1": (806, 90, 0), "o2": (817, 81, 0), "o3": (822, 97, 0), "o4": (808, 106, 0), "o5": (797, 98, 0),
             "g1": (852, 126, 1), "g2": (862, 114, 1), "g3": (866, 132, 1), "g4": (850, 142, 1), "g5": (840, 131, 1),
             "y1": (860, 92, 2), "y2": (869, 101, 2), "y3": (853, 104, 2)}
    edges = [("o1", "o2"), ("o2", "o3"), ("o3", "o4"), ("o4", "o5"), ("o5", "o1"), ("o1", "o3"),
             ("g1", "g2"), ("g2", "g3"), ("g3", "g4"), ("g4", "g5"), ("g5", "g1"), ("g1", "g3"),
             ("y1", "y2"), ("y2", "y3"), ("y3", "y1"), ("o3", "y3"), ("o3", "g5"), ("y3", "g2"), ("o4", "g5")]
    sel = "o3"
    nbrs = {b if a == sel else a for a, b in edges if sel in (a, b)} | {sel}
    for a, b in edges:
        (x1, y1, _), (x2, y2, _) = nodes[a], nodes[b]
        on = sel in (a, b)
        add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{ACCENT if on else "#c4c3bd"}" '
            f'stroke-width="{1.3 if on else 0.9}" opacity="{1 if on else 0.6}"/>')
    for k, (x, y, g) in nodes.items():
        add(f'<circle cx="{x}" cy="{y}" r="3.4" fill="{FIELDS[g]}" stroke="#fff" stroke-width="0.8" '
            f'opacity="{1 if k in nbrs else 0.35}"/>')
    x, y, _ = nodes[sel]
    add(f'<circle cx="{x}" cy="{y}" r="6" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>')
    # tooltip on hover
    add(f'<rect x="828" y="68" width="40" height="15" rx="2" fill="{INK}"/>')
    add('<path d="M831,83 L826,90 L837,83 Z" fill="#1f2328"/>')
    add('<path d="M832,73 H860 M832,78.5 H850" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/>')
    icon("cursor", 823, 98.5, 12, INK)


def draw_bundling_view() -> None:
    cx, cy, r = 929, 112, 29
    groups = [list(range(0, 6)), list(range(6, 12)), list(range(12, 18))]
    for g, ks in enumerate(groups):  # group arcs
        a0, a1 = math.radians(-90 + ks[0] * 20 - 8), math.radians(-90 + ks[-1] * 20 + 8)
        R = r + 5
        add(f'<path d="M{cx + R * math.cos(a0):.1f},{cy + R * math.sin(a0):.1f} A{R},{R} 0 0 1 '
            f'{cx + R * math.cos(a1):.1f},{cy + R * math.sin(a1):.1f}" fill="none" stroke="{FIELDS[g]}" '
            f'stroke-width="3.2" stroke-linecap="round" opacity="0.85"/>')

    def centroid(g, rad):
        return node_xy(cx, cy, rad, 2.5 + 6 * g)

    edges = [(1, 8), (2, 9), (3, 14), (4, 15), (0, 13), (7, 16), (10, 17), (5, 12), (2, 6), (2, 14), (11, 13),
             (1, 4), (8, 10), (13, 16)]
    sel = 2
    for a, b in sorted(edges, key=lambda e: sel in e):
        ga, gb = a // 6, b // 6
        p, q = node_xy(cx, cy, r, a), node_xy(cx, cy, r, b)
        c1, c2 = (centroid(ga, 17), centroid(gb, 17)) if ga == gb else (centroid(ga, 9), centroid(gb, 9))
        on = sel in (a, b)
        add(f'<path d="M{p[0]:.1f},{p[1]:.1f} C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} '
            f'{q[0]:.1f},{q[1]:.1f}" fill="none" stroke="{ACCENT if on else "#b9b8b2"}" '
            f'stroke-width="{1.3 if on else 0.9}" opacity="{1 if on else 0.55}"/>')
    for k in range(18):
        x, y = node_xy(cx, cy, r, k)
        on = k == sel or any(sel in e and k in e for e in edges)
        add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{FIELDS[k // 6]}" stroke="#fff" '
            f'stroke-width="0.6" opacity="{1 if on else 0.4}"/>')
    x, y = node_xy(cx, cy, r, sel)
    add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.2" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>')


def draw_app() -> None:
    panel(706, 10, 284, 324, 3, "Interactive web app")
    # browser window
    rect(716, 44, 264, 184, rx=6, fill="#fff", stroke="none")
    add('<g clip-path="url(#win)"><rect x="716" y="44" width="264" height="14" fill="#efeee9"/></g>')
    add('<line x1="716" y1="58" x2="980" y2="58" stroke="#dcdbd5" stroke-width="1"/>')
    for i in range(3):
        add(f'<circle cx="{725 + 8 * i}" cy="51" r="2.3" fill="#c9c8c2"/>')
    rect(716, 44, 264, 184, rx=6, fill="none", stroke="#c4c3bd")
    # chat column
    add('<line x1="782" y1="58" x2="782" y2="228" stroke="#e6e5e0" stroke-width="1"/>')
    rect(744, 64, 32, 12, rx=4, fill=ACCENT_TINT, stroke="none")
    rect(722, 82, 50, 24, rx=4, fill="#f2f1ec", stroke="none")
    add('<path d="M727,90 H766 M727,98 H754" stroke="#c4c3bd" stroke-width="1.6" stroke-linecap="round"/>')
    rect(736, 112, 40, 13, rx=4, fill=ACCENT_TINT, stroke="none")
    add(f'<circle cx="742" cy="118.5" r="2.6" fill="{ACCENT}"/>')
    add(f'<path d="M748,118.5 H770" stroke="{ACCENT}" stroke-width="1.6" stroke-linecap="round" opacity="0.6"/>')
    rect(722, 131, 50, 20, rx=4, fill="#f2f1ec", stroke="none")
    add('<path d="M727,138 H766 M727,145 H748" stroke="#c4c3bd" stroke-width="1.6" stroke-linecap="round"/>')
    rect(722, 208, 54, 14, rx=4, fill="#fff", stroke="#d6d5cf", sw=0.9)
    # two linked views
    for tx in (788, 884):
        rect(tx, 64, 90, 92, rx=4, fill="#fff", stroke="#dcdbd5", sw=0.9)
        add(f'<path d="M{tx},74 V68 a4,4 0 0 1 4,-4 H{tx + 86} a4,4 0 0 1 4,4 V74 Z" fill="#f3f2ee"/>')
        add(f'<path d="M{tx + 5},69 H{tx + 36}" stroke="#bdbcb6" stroke-width="1.6" stroke-linecap="round"/>')
    draw_force_view()
    draw_bundling_view()
    text(833, 167, "force layout", "note", "middle")
    text(929, 167, "edge bundling", "note", "middle")
    # generated parameter controls
    add('<path d="M794,182 H848" stroke="#d6d5cf" stroke-width="2.2" stroke-linecap="round"/>')
    add(f'<path d="M794,182 H826" stroke="{ACCENT}" stroke-width="2.2" stroke-linecap="round"/>')
    add(f'<circle cx="826" cy="182" r="4" fill="#fff" stroke="{ACCENT}" stroke-width="1.4"/>')
    rect(860, 175, 52, 14, rx=3, fill="#fff", stroke="#c9c8c2", sw=0.9)
    add('<path d="M865,182 H890" stroke="#bdbcb6" stroke-width="1.6" stroke-linecap="round"/>')
    add(f'<path d="M899,180 L902.5,184 L906,180" fill="none" stroke="{MUTED}" stroke-width="1.2"/>')
    rect(922, 176, 22, 12, rx=6, fill=ACCENT, stroke="none")
    add('<circle cx="938" cy="182" r="4.2" fill="#fff"/>')
    text(794, 206, 'controls generated from <tspan class="mono">viz.json</tspan>', "note", raw=True)

    lines(848, 243, ["hover → details · click → select & link",
                     "versions · undo · side-by-side compare"], lh=13, cls="small", anchor="middle")
    # the generic contract every agent-written view implements
    rect(716, 264, 264, 64, rx=6, fill="#fff", stroke="#c9c8c2")
    text(726, 280, "Generic view contract", "box-s")
    text(972, 280, "sandboxed iframe", "small", "end")
    text(726, 295, "render(el, ctx) →", "mono")
    text(738, 308, "update · setSelection · highlight", "mono")
    text(726, 322, "marks carry data-id → hover, select, link", "small")


# ---------------------------------------------------------------------------------------------------------------
def draw_flows_and_services() -> None:
    # question in, data access
    arrow("M150,92 C188,92 190,81 228,81", "blue", 1.4)
    lines(198, 108, ["question", "+ selection"], lh=12, cls="note", anchor="middle", fill=ACCENT_DARK)
    arrow("M107,198 H174", "grey", 1.2)
    text(140, 192, "query", "note", "middle")
    # the Lead's answer and the approved views go to the app
    arrow("M455,70 H714", "grey", 1.3)
    add(f'<circle cx="630" cy="70" r="2.6" fill="{ROLE["analyst"][0]}"/>')
    text(540, 63, "answer + approved views", "note", "middle")
    # user feedback loop: from the app back into the harness
    arrow("M760,335 V352 H342 V331", "blue", 1.4, dash="4 3")
    rect(436, 345, 230, 14, rx=3, fill="#fff", stroke="none")
    text(551, 355.5, "follow-up question + current selection", "note", "middle", fill=ACCENT_DARK)

    # harness services
    rect(10, 370, 980, 82, rx=10, fill="#f1f0ec", stroke="#dcdbd5")
    rect(20, 362, 132, 18, rx=5, fill=INK, stroke="none")
    text(86, 375, "Harness services", "box-s", "middle", fill="#fff")
    items = [("layers", "Deep Agents", ["on LangGraph,", "isolated contexts"]),
             ("term", "Python kernels", ["one per agent,", "secrets stripped"]),
             ("db", "DuckDB SQL", ["read-only,", "with timeout"]),
             ("pkg", "npm discovery", ["package docs,", "pinned imports"]),
             ("log", "Event log", ["live trace", "and replay"]),
             ("retry", "Recovery", ["checkpoints, retry,", "model escalation"]),
             ("coin", "Budget", ["spend ledger,", "call limits"])]
    for i, (ic, title, sub) in enumerate(items):
        x0 = 30 + i * 137
        icon(ic, x0 + 2, 392, 22, "#4a4945")
        text(x0 + 30, 400, title, "box-s")
        lines(x0 + 30, 414, sub, lh=12.5, cls="small")


def build_svg() -> str:
    out.clear()
    draw_input()
    draw_harness()
    draw_app()
    draw_flows_and_services()
    defs = (f"<defs><style>{STYLE}</style>{SYMBOLS}{markers()}"
            '<clipPath id="win"><rect x="716" y="44" width="264" height="184" rx="6"/></clipPath></defs>')
    body = "\n".join(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{WIDTH_IN}in" '
            f'height="{HEIGHT_IN}in">\n{defs}\n<rect width="{W}" height="{H}" fill="#fff"/>\n{body}\n</svg>\n')


def render(svg: str) -> None:
    from playwright.sync_api import sync_playwright

    html = ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;padding:0}"
            f"svg{{display:block;width:{WIDTH_IN}in;height:{HEIGHT_IN}in}}</style></head><body>{svg}</body></html>")
    px_w, px_h = round(WIDTH_IN * 96), round(HEIGHT_IN * 96)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": px_w, "height": px_h}, device_scale_factor=300 / 96)
        page.set_content(html)
        page.pdf(path=str(HERE / f"{NAME}.pdf"), width=f"{WIDTH_IN}in", height=f"{HEIGHT_IN}in",
                 print_background=True, page_ranges="1")
        page.screenshot(path=str(HERE / f"{NAME}.png"), clip={"x": 0, "y": 0, "width": px_w, "height": px_h})
        browser.close()


if __name__ == "__main__":
    svg = build_svg()
    (HERE / f"{NAME}.svg").write_text(svg)
    render(svg)
    print(f"wrote {NAME}.svg/.pdf/.png in {HERE} ({WIDTH_IN} x {HEIGHT_IN} in)")
