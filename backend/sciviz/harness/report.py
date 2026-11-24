"""Report assembly, evidence checks and PDF rendering (report mode, PLAN_P2 §3.3, §5).

The Writer saves Markdown sections under report/sections/. A report is assembled from them in order, checked
mechanically (every cited id exists, every figure is approved, statistics carry a citation), reviewed by an
independent reviewer (tools/report_tools.py), and rendered to HTML and PDF with Playwright.

Markup the Writer uses:
- citations: [T3], [F2, T5] (artifact ids), or [brief] for facts about the original study;
- figures: {{figure:P4}} on its own line (an approved figure artifact); numbered in order of appearance.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from markdown_it import MarkdownIt

CITE = re.compile(r"\[((?:[TGHJFVP]\d+|brief)(?:\s*,\s*(?:[TGHJFVP]\d+|brief))*)\]")
FIG = re.compile(r"\{\{\s*figure:\s*([A-Z]\d+)\s*\}\}")
# Statistic-like numbers: decimals, percentages, and integers >= 100 that are not years.
STAT = re.compile(r"(?<![\w.])(?:\d+\.\d+|\d+(?:\.\d+)?\s?%|\d{1,3}(?:,\d{3})+|\d{3,})(?![\w])")
YEAR = re.compile(r"^(1[89]\d\d|20\d\d)$")
SECTION_FILE = re.compile(r"^(\d+)_([a-z0-9_-]+)\.md$")


def sections_dir(root: Path) -> Path:
    d = root / "report" / "sections"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_sections(root: Path) -> list[tuple[int, str, Path]]:
    out = []
    for p in sections_dir(root).glob("*.md"):
        m = SECTION_FILE.match(p.name)
        if m:
            out.append((int(m.group(1)), m.group(2), p))
    return sorted(out)


def assemble(root: Path, title: str) -> str:
    parts = [f"# {title}"]
    parts += [p.read_text(encoding="utf8").strip() for _, _, p in list_sections(root)]
    return "\n\n".join(parts) + "\n"


def _blocks(md: str) -> list[tuple[str, str]]:
    """Split Markdown into (kind, text) blocks: heading, table, code, figure, para."""
    blocks, buf, in_code = [], [], False

    def flush():
        if buf:
            text = "\n".join(buf).strip()
            if text:
                kind = "table" if text.lstrip().startswith("|") else "para"
                blocks.append((kind, text))
            buf.clear()

    for line in md.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                buf.append(line)
                blocks.append(("code", "\n".join(buf)))
                buf.clear()
                in_code = False
            else:
                flush()
                in_code = True
                buf.append(line)
            continue
        if in_code:
            buf.append(line)
        elif line.startswith("#"):
            flush()
            blocks.append(("heading", line))
        elif FIG.fullmatch(line.strip() or "x"):
            flush()
            blocks.append(("figure", line.strip()))
        elif not line.strip():
            flush()
        else:
            if buf and (buf[0].lstrip().startswith("|") != line.lstrip().startswith("|")):
                flush()
            buf.append(line)
    flush()
    return blocks


def stats_without_citation(md: str) -> list[str]:
    problems = []
    blocks = _blocks(md)
    for i, (kind, text) in enumerate(blocks):
        if kind not in ("para", "table"):
            continue
        nums = [n for n in STAT.findall(CITE.sub("", FIG.sub("", text))) if not YEAR.match(n)]
        if not nums:
            continue
        cited = CITE.search(text)
        if kind == "table" and not cited:  # a table may be cited in the sentence just before or after it
            near = [blocks[j][1] for j in (i - 1, i + 1) if 0 <= j < len(blocks) and blocks[j][0] == "para"]
            cited = any(CITE.search(t) for t in near)
        if not cited:
            snippet = re.sub(r"\s+", " ", text)[:160]
            problems.append(f"numbers {nums[:4]} have no citation in: \"{snippet}\"")
    return problems


def check(md: str, artifacts: dict[str, dict]) -> list[str]:
    """Mechanical checks; `artifacts` maps id -> meta for every artifact in the session."""
    problems = []
    for m in CITE.finditer(md):
        for ident in (x.strip() for x in m.group(1).split(",")):
            if ident != "brief" and ident not in artifacts:
                problems.append(f"cited id {ident} does not exist")
    figs = FIG.findall(md)
    for fid in figs:
        meta = artifacts.get(fid)
        if not meta or meta["kind"] != "figure":
            problems.append(f"{{{{figure:{fid}}}}} is not a figure artifact")
        elif meta.get("status") not in ("approved", "approved_with_issues"):
            problems.append(f"figure {fid} has not passed the figure gate (status {meta.get('status')})")
    if len(figs) != len(set(figs)):
        problems.append("a figure is placed more than once")
    problems += stats_without_citation(md)
    return list(dict.fromkeys(problems))


CSS = """
@page { size: Letter; margin: 0.9in 0.85in; }
body { font-family: 'Charter', 'Georgia', serif; font-size: 10.5pt; line-height: 1.42; color: #111; }
h1 { font-size: 19pt; line-height: 1.2; margin: 0 0 4pt; }
.subtitle { color: #555; font-size: 9.5pt; margin-bottom: 18pt; }
h2 { font-size: 13pt; margin: 18pt 0 6pt; border-bottom: 0.6pt solid #bbb; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; }
p { margin: 0 0 7pt; text-align: justify; hyphens: auto; }
table { border-collapse: collapse; margin: 8pt 0 10pt; font-size: 8.8pt; width: 100%; page-break-inside: avoid; }
th, td { border-bottom: 0.5pt solid #ccc; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { border-bottom: 1pt solid #333; }
figure { margin: 10pt 0 12pt; page-break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 6.2in; }
figcaption { font-size: 9pt; color: #222; text-align: left; margin-top: 4pt; }
.cite { color: #2a5d9f; font-size: 8.5pt; white-space: nowrap; }
code, pre { font-family: Menlo, monospace; font-size: 8.5pt; }
pre { background: #f5f5f5; padding: 6pt; white-space: pre-wrap; }
.evidence td:first-child { white-space: nowrap; font-family: Menlo, monospace; }
"""


def to_html(md: str, artifacts: dict[str, dict], root: Path, subtitle: str = "") -> str:
    order: dict[str, int] = {}

    def fig_html(m: re.Match) -> str:
        fid = m.group(1)
        order.setdefault(fid, len(order) + 1)
        meta = artifacts[fid]
        src = (root / "artifacts" / fid / "figure.png").resolve().as_uri()
        cap = html.escape(meta.get("description", ""))
        return (f'\n<figure><img src="{src}"><figcaption><b>Figure {order[fid]}.</b> '
                f'<b>{html.escape(meta["title"])}.</b> {cap} <span class="cite">[{fid}]</span></figcaption></figure>\n')

    body_md = FIG.sub(fig_html, md)
    # Text references such as "Figure P4" become "Figure 2".
    body_md = re.sub(r"\b(Fig(?:ure|\.)?)\s+([A-Z]\d+)\b",
                     lambda m: f"{m.group(1)} {order[m.group(2)]}" if m.group(2) in order else m.group(0), body_md)
    body = MarkdownIt("commonmark", {"html": True}).enable("table").render(body_md)
    body = CITE.sub(lambda m: f'<span class="cite">[{m.group(1)}]</span>', body)
    if subtitle:
        body = body.replace("</h1>", f'</h1>\n<div class="subtitle">{html.escape(subtitle)}</div>', 1)
    cited = []
    for m in CITE.finditer(md):
        cited += [x.strip() for x in m.group(1).split(",") if x.strip() != "brief"]
    cited = list(dict.fromkeys(cited + list(order)))
    rows = "".join(
        f"<tr><td>{c}</td><td>{html.escape(artifacts[c]['kind'])}</td><td>{html.escape(artifacts[c]['title'])}"
        f"</td><td>{html.escape((artifacts[c].get('description') or '')[:220])}</td></tr>"
        for c in cited if c in artifacts)
    evidence = (f'<h2>Evidence index</h2><p>Every artifact cited above, with its kind and description. Code, data and '
                f'lineage for each are in the run\'s workspace and in the exported scripts.</p><table class="evidence">'
                f"<tr><th>ID</th><th>Kind</th><th>Title</th><th>Description</th></tr>{rows}</table>") if rows else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
            f"<body>{body}{evidence}</body></html>")


def render_pdf(html_text: str, html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    html_path.write_text(html_text, encoding="utf8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.pdf(path=str(pdf_path), format="Letter", print_background=True,
                 margin={"top": "0.9in", "bottom": "0.9in", "left": "0.85in", "right": "0.85in"},
                 display_header_footer=True, header_template="<span></span>",
                 footer_template="<div style='font-size:8pt;color:#777;width:100%;text-align:center'>"
                                 "<span class='pageNumber'></span> / <span class='totalPages'></span></div>")
        browser.close()


def evidence_text(artifacts: dict[str, dict], root: Path, limit: int = 60000) -> str:
    """Findings in full, plus one-line summaries of all other artifacts (input for the report reviewer)."""
    parts = []
    for aid, m in artifacts.items():
        if m["kind"] == "finding":
            try:
                data = json.loads((root / "artifacts" / aid / "data.json").read_text())
                parts.append(f"{aid} (finding) {data.get('text')} | value: {json.dumps(data.get('value'), default=str)[:800]}")
            except (OSError, json.JSONDecodeError):
                parts.append(f"{aid} (finding) {m['title']}")
    for aid, m in artifacts.items():
        if m["kind"] != "finding":
            short = m["summary"] if isinstance(m["summary"], str) else m["summary"].get("text", "")[:900]
            status = f" [{m.get('status')}]" if m["kind"] in ("figure", "viz") else ""
            parts.append(f"{aid} ({m['kind']}{status}) {m['title']}: {m.get('description', '')[:400]}\n{short}")
    text = "\n\n".join(parts)
    return text if len(text) <= limit else text[:limit] + "\n... [evidence truncated]"
