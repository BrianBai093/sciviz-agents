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

from figure_kit import (ACCENT, ACCENT_DARK, ACCENT_TINT, FIELDS, GREEN_DARK, INK, LINE, MUTED, ROLE, add, arrow,
                        icon, lines, out, panel, rect, render, svg_document, text)

HERE = Path(__file__).resolve().parent
NAME = "sciviz_architecture"
W, H = 1000, 460  # drawing units
WIDTH_IN = 7.0  # printed width
HEIGHT_IN = round(WIDTH_IN * H / W, 3)

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
    return svg_document(W, H, WIDTH_IN, '<clipPath id="win"><rect x="716" y="44" width="264" height="184" rx="6"/></clipPath>')


if __name__ == "__main__":
    svg = build_svg()
    (HERE / f"{NAME}.svg").write_text(svg)
    render(svg, HERE, NAME, WIDTH_IN, HEIGHT_IN)
    print(f"wrote {NAME}.svg/.pdf/.png in {HERE} ({WIDTH_IN} x {HEIGHT_IN} in)")
