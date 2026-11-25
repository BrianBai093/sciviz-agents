"""Build the report-mode figure (Design Test, Option A, Project 2): a paper-style overview of how the agents
reproduce a published study.

    uv run python docs/figures/build_reproduce_figure.py

The drawing code below writes the SVG (the source of truth); `figure_kit.render` turns it into a vector PDF (7 in wide,
fonts embedded) and a 300 dpi PNG. Layout, agreed with the user (D60): (1) input -> (2) report-mode harness with two
verification gates -> (3) report and reproduction package, the user's loop over turns along the top, and the harness
services along the bottom. It describes the design, not one run: no run-specific numbers.
"""
from __future__ import annotations

from pathlib import Path

from figure_kit import (
    ACCENT,
    ACCENT_DARK,
    ACCENT_TINT,
    EXTRA_SYMBOLS,
    GREEN_DARK,
    INK,
    LINE,
    MUTED,
    ROLE,
    add,
    arrow,
    icon,
    lines,
    out,
    panel,
    rect,
    render,
    svg_document,
    text,
)

HERE = Path(__file__).resolve().parent
NAME = "sciviz_reproduce"
W, H = 1000, 480  # drawing units
WIDTH_IN = 7.0  # printed width
HEIGHT_IN = round(WIDTH_IN * H / W, 3)
PT = 38  # top of the three panels; the user's loop runs above them
PH = 330  # panel height
ROLE = {**ROLE, "writer": ROLE["viz"]}  # the writer, like Project 1's viz agent, makes what the user receives
GREEN_TINT = "#e9f5ec"
STATUS = [("reproduced", ROLE["analyst"][0]), ("partly reproduced", ROLE["viz"][0]),
          ("not reproduced", ROLE["critic"][0]), ("not testable", "#9a9993")]
ICON_INK = "#4a4945"


def numbered(x, y, n, color) -> None:
    add(f'<circle cx="{x}" cy="{y - 3.7}" r="5" fill="{color}"/>')
    text(x, y - 1, str(n), "tiny", "middle")


# ---------------------------------------------------------------------------------------------------------------
# (1) Input
def draw_input() -> None:
    panel(10, PT, 150, PH, 1, "Input")
    icon("user", 18, PT + 30, 20, MUTED)
    text(43, PT + 45, "User", "box-s")
    rect(18, PT + 56, 134, 72, rx=6, fill="#fff", stroke=LINE)
    add(f'<path d="M26,{PT + 56.6} L29,{PT + 49.5} L35,{PT + 56.6}" fill="#fff" stroke="{LINE}" stroke-width="1" '
        'stroke-linejoin="round"/>')
    lines(25, PT + 71, ["“How does team size", "influence the balance", "between disruptive",
                        "and developmental", "research?”"], lh=12.6, cls="quote")
    rect(18, PT + 134, 134, 18, rx=9, fill=ACCENT_TINT, stroke=ACCENT, sw=0.8)
    icon("log", 24, PT + 136.5, 13, ACCENT)
    text(40, PT + 146.8, "+ run constraints", "small", fill=ACCENT_DARK)

    icon("doc", 18, PT + 161, 24, ICON_INK)
    text(46, PT + 173, "Paper brief", "box-s")
    lines(46, PT + 186, ["claims, measures and", "methods, in our words"], lh=12, cls="small")
    icon("db", 20, PT + 214, 26, ROLE["data"][0])
    text(52, PT + 225, "Local snapshot", "box-s")
    text(52, PT + 238, "read-only SQL", "small")
    icon("globe", 20, PT + 252, 26, ROLE["data"][0])
    text(52, PT + 263, "OpenAlex API", "box-s")
    text(52, PT + 276, "via the harness proxy", "small")
    text(85, PT + 316, "datasets are pluggable", "note", "middle")


# ---------------------------------------------------------------------------------------------------------------
# (2) Report-mode harness
def agent_box(role, x, y, w, h, title, body, mono=None) -> None:
    s, t = ROLE[role]
    rect(x, y, w, h, rx=8, fill=t, stroke=s, sw=1.3)
    icon("robot", x + 8, y + 6, 20, s)
    text(x + 33, y + 21, title, "box")
    lines(x + 10, y + 38, body, lh=13)
    if mono:
        text(x + 10, y + 38 + 13 * len(body) + 2, mono, "mono")


def draw_harness() -> None:
    panel(170, PT, 520, PH, 2, "Report-mode harness")
    rect(450, PT + 8, 232, 18, rx=9, fill=GREEN_TINT, stroke=ROLE["analyst"][0], sw=0.8)
    icon("check", 455, PT + 10.5, 13, ROLE["analyst"][0])
    text(473, PT + 20.8, "no study-specific prompts or code", "small", fill=GREEN_DARK)

    # Lead
    s, t = ROLE["lead"]
    rect(196, PT + 36, 236, 56, rx=8, fill=t, stroke=s, sw=1.3)
    icon("robot", 205, PT + 44, 24, s)
    text(238, PT + 55, "Lead agent", "box")
    lines(238, PT + 70, ["brief → claim plan", "delegates · checks reports"], lh=13.5)

    # specialists
    agent_box("data", 180, PT + 108, 104, 168, "Data",
              ["designs and", "pilots the data", "collection,", "checks counts;", "long runs as", "background jobs"],
              "openalex()")
    agent_box("analyst", 300, PT + 108, 148, 54, "Analyst", ["measures, statistics,"], None)
    text(310, PT + 159, "models, figures", "body")
    agent_box("writer", 300, PT + 188, 148, 54, "Writer", ["plain-language report;"], None)
    text(310, PT + 239, "every number cited", "body")

    # Lead delegates: to the Data agent, and along a bus to the Analyst and the Writer
    arrow(f"M232,{PT + 93} V{PT + 106}", "grey", 1.1, start=True, small=True)
    arrow(f"M291,{PT + 93} V{PT + 215}", "grey", 1.1, end=False)
    arrow(f"M291,{PT + 135} H298", "grey", 1.1, small=True)
    arrow(f"M291,{PT + 215} H298", "grey", 1.1, small=True)
    text(300, PT + 103, "brief / report", "note")

    # artifact store
    rect(180, PT + 292, 502, 30, rx=8, fill="#fff", stroke=LINE)
    for i, n in enumerate(("table", "graph", "doc", "code")):
        icon(n, 188 + i * 21, PT + 297, 19, MUTED)
    text(278, PT + 311.5, "Shared artifact store", "box-s")
    text(410, PT + 311.5, "each result with its code and lineage", "small")
    arrow(f"M232,{PT + 277} V{PT + 290}", "grey", 1, start=True, small=True)
    arrow(f"M374,{PT + 243} V{PT + 290}", "grey", 1, start=True, small=True)

    # verification gates
    s, t = ROLE["critic"]
    rect(492, PT + 36, 190, 246, rx=8, fill=t, stroke=s, sw=1.3)
    icon("shield", 500, PT + 42, 22, s)
    text(528, PT + 56, "Verification gates", "box")
    text(528, PT + 71, "enforced by the harness", "note")

    rect(500, PT + 82, 174, 80, rx=6, fill="#fff", stroke=s, sw=0.9)
    text(508, PT + 98, "Figure gate", "box-s")
    icon("robot", 652, PT + 86, 15, s)
    numbered(513, PT + 114, 1, s)
    text(523, PT + 114, "file checks", "small")
    numbered(513, PT + 128, 2, s)
    lines(523, PT + 128, ["critic sees the image:", "does it test the claim?"], lh=12, cls="small")
    numbered(513, PT + 154, 3, s)
    text(523, PT + 154, "plain labels and caption", "small")

    rect(500, PT + 170, 174, 104, rx=6, fill="#fff", stroke=s, sw=0.9)
    text(508, PT + 186, "Report gate", "box-s")
    icon("robot", 652, PT + 174, 15, s)
    numbered(513, PT + 202, 1, s)
    lines(523, PT + 202, ["numbers cite evidence,", "figures are approved"], lh=12, cls="small")
    numbered(513, PT + 230, 2, s)
    lines(523, PT + 230, ["reviewer checks the text", "against all evidence"], lh=12, cls="small")
    numbered(513, PT + 258, 3, s)
    lines(523, PT + 258, ["reader sees only the", "report: can it be followed?"], lh=12, cls="small")

    # submit / revise loops
    for y, color in ((PT + 124, "green"), (PT + 205, "amber")):
        arrow(f"M449,{y} H498", color, 1.3)
        arrow(f"M498,{y + 26} H451", "red", 1.3, dash="3 2")
        icon("retry", 456, y + 5, 13, ROLE["critic"][0])
        text(473, y + 15.5, "×N", "small-b", fill=ROLE["critic"][0])
    text(474, PT + 118, "submit", "note", "middle")
    text(474, PT + 199, "submit", "note", "middle")

    # approved figures go into the report
    arrow(f"M506,{PT + 163} C490,{PT + 176} 462,{PT + 172} 440,{PT + 186}", "green", 1.3)
    text(436, PT + 177, "approved figures", "small-b", "end", fill="#2e7d32")


# ---------------------------------------------------------------------------------------------------------------
# (3) Report and reproduction package
def draw_output() -> None:
    panel(700, PT, 290, PH, 3, "Report and package")
    # an abstract report page
    x0, y0 = 712, PT + 36
    rect(x0, y0, 92, 160, rx=3, fill="#fff", stroke="#c4c3bd")
    add(f'<path d="M{x0 + 8},{y0 + 12} H{x0 + 68}" stroke="#8a8984" stroke-width="3" stroke-linecap="round"/>')
    add(f'<path d="M{x0 + 8},{y0 + 22} H{x0 + 84} M{x0 + 8},{y0 + 29} H{x0 + 64}" stroke="#c9c8c2" '
        'stroke-width="1.6" stroke-linecap="round"/>')
    # a small chart with error bars
    cx, cy = x0 + 12, y0 + 38
    add(f'<path d="M{cx},{cy} V{cy + 40} H{cx + 70}" fill="none" stroke="#8a8984" stroke-width="1"/>')
    pts = [(cx + 8, cy + 9), (cx + 20, cy + 15), (cx + 32, cy + 17), (cx + 44, cy + 20), (cx + 56, cy + 27),
           (cx + 66, cy + 32)]
    add('<polyline points="' + " ".join(f"{x},{y}" for x, y in pts) + f'" fill="none" stroke="{ACCENT}" '
        'stroke-width="1.3"/>')
    for x, y in pts:
        add(f'<path d="M{x},{y - 4} V{y + 4}" stroke="{ACCENT}" stroke-width="0.9"/>')
        add(f'<circle cx="{x}" cy="{y}" r="1.8" fill="{ACCENT}"/>')
    add(f'<path d="M{x0 + 8},{y0 + 90} H{x0 + 84} M{x0 + 8},{y0 + 97} H{x0 + 72}" stroke="#c9c8c2" '
        'stroke-width="1.6" stroke-linecap="round"/>')
    # the verdict table
    for i, (_, color) in enumerate(STATUS):
        y = y0 + 110 + i * 11
        add(f'<path d="M{x0 + 8},{y} H{x0 + 50}" stroke="#d6d5cf" stroke-width="1.6" stroke-linecap="round"/>')
        add(f'<circle cx="{x0 + 62}" cy="{y}" r="3" fill="{color}"/>')
    add(f'<path d="M{x0 + 8},{y0 + 152} H{x0 + 60}" stroke="#d6d5cf" stroke-width="1.6" stroke-linecap="round"/>')

    text(816, PT + 52, "Report (PDF)", "box-s")
    lines(816, PT + 67, ["one section per finding", "of the study: its result,", "ours, and a verdict:"], lh=13,
          cls="small")
    for i, (label, color) in enumerate(STATUS):
        y = PT + 110 + i * 14
        add(f'<circle cx="{822}" cy="{y - 3.5}" r="3.5" fill="{color}"/>')
        text(831, y, label, "small")
    lines(816, PT + 176, ["plain language; every", "number cites its source"], lh=13, cls="small")

    # the package and the replay
    icon("pkg", 712, PT + 214, 28, ICON_INK)
    text(748, PT + 226, "Reproduction package", "box-s")
    lines(748, PT + 241, ["every result with its code", "every code step, in order", "frozen API responses",
                          "run record by the harness"], lh=12.5, cls="small")
    rect(712, PT + 292, 270, 30, rx=6, fill=GREEN_TINT, stroke=ROLE["analyst"][0], sw=0.8)
    icon("retry", 719, PT + 299, 16, ROLE["analyst"][0])
    text(742, PT + 304.5, "Offline replay", "small-b", fill=GREEN_DARK)
    text(742, PT + 316.5, "reruns every step; compares every result", "small", fill=GREEN_DARK)


# ---------------------------------------------------------------------------------------------------------------
def draw_flows_and_services() -> None:
    # into the Lead: the question and the brief
    arrow(f"M152,{PT + 84} C176,{PT + 84} 176,{PT + 56} 194,{PT + 56}", "blue", 1.4)
    arrow(f"M156,{PT + 175} C178,{PT + 175} 168,{PT + 82} 194,{PT + 80}", "grey", 1.2)
    # the Data agent reaches both data sources
    arrow(f"M146,{PT + 227} H178", "grey", 1.2, start=True, small=True)
    arrow(f"M146,{PT + 265} H178", "grey", 1.2, start=True, small=True)
    # released report, exported package
    arrow(f"M674,{PT + 186} H710", "green", 1.4)
    arrow(f"M682,{PT + 307} H695 V{PT + 228} H710", "grey", 1.2)
    text(676, PT + 304, "export", "note", "end")

    # the user's loop over turns
    arrow(f"M940,{PT} V16 H125 V{PT - 1}", "blue", 1.4, dash="4 3")
    rect(300, 9, 470, 14, rx=3, fill="#fff", stroke="none")
    text(535, 20, "user reads the report → constraints for the next turn: pilot → full run → corrections → rewrite",
         "note", "middle", fill=ACCENT_DARK)

    # harness services
    y = PT + PH + 20
    rect(10, y + 8, 980, 82, rx=10, fill="#f1f0ec", stroke="#dcdbd5")
    rect(20, y, 132, 18, rx=5, fill=INK, stroke="none")
    text(86, y + 13, "Harness services", "box-s", "middle", fill="#fff")
    items = [("layers", "Deep Agents", ["on LangGraph,", "with checkpoints"]),
             ("term", "Python kernels", ["one per agent,", "secrets stripped"]),
             ("globe", "OpenAlex service", ["local proxy, cache,", "rate limit, budget"]),
             ("clock", "Background jobs", ["long collections,", "logged step by step"]),
             ("log", "Cell & file log", ["every code step", "and file write"]),
             ("pkg", "Export & replay", ["package, run record,", "offline rerun"]),
             ("coin", "Budget", ["LLM ledger,", "API spend cap"])]
    for i, (ic, title, sub) in enumerate(items):
        x0 = 30 + i * 137
        icon(ic, x0 + 2, y + 30, 22, ICON_INK)
        text(x0 + 30, y + 38, title, "box-s")
        lines(x0 + 30, y + 52, sub, lh=12.5, cls="small")


def build_svg() -> str:
    out.clear()
    draw_input()
    draw_harness()
    draw_output()
    draw_flows_and_services()
    return svg_document(W, H, WIDTH_IN, EXTRA_SYMBOLS)


if __name__ == "__main__":
    svg = build_svg()
    (HERE / f"{NAME}.svg").write_text(svg)
    render(svg, HERE, NAME, WIDTH_IN, HEIGHT_IN)
    print(f"wrote {NAME}.svg/.pdf/.png in {HERE} ({WIDTH_IN} x {HEIGHT_IN} in)")
