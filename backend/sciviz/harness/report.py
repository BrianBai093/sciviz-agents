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
from collections import Counter
from datetime import datetime, timezone
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
h2, h3 { break-after: avoid; page-break-after: avoid; }
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


def to_html(md: str, artifacts: dict[str, dict], root: Path, subtitle: str = "", img_src=None) -> str:
    """`img_src(figure_id) -> str` sets the image URL (default: the figure's file in the workspace)."""
    order: dict[str, int] = {}

    def fig_html(m: re.Match) -> str:
        fid = m.group(1)
        order.setdefault(fid, len(order) + 1)
        meta = artifacts[fid]
        src = img_src(fid) if img_src else (root / "artifacts" / fid / "figure.png").resolve().as_uri()
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
        f"</td></tr>" for c in cited if c in artifacts)
    evidence = (f'<h2>Evidence index</h2><p>The ids in square brackets point to the saved results behind each '
                f'statement. This list gives each one under the title the agents gave it while working. The data, the '
                f'code that produced it and its inputs are in the reproduction package, under '
                f'<code>data/artifacts/&lt;id&gt;/</code>.</p><table class="evidence">'
                f"<tr><th>ID</th><th>Kind</th><th>Title</th></tr>{rows}</table>") if rows else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
            f"<body>{body}{evidence}</body></html>")


def reader_text(md: str, artifacts: dict[str, dict]) -> str:
    """The report as a reader sees it: each figure placeholder becomes its numbered title and caption, and text
    references such as "Figure P4" become "Figure 2" (input for the report gate's reader check)."""
    order: dict[str, int] = {}

    def fig(m: re.Match) -> str:
        fid = m.group(1)
        order.setdefault(fid, len(order) + 1)
        meta = artifacts.get(fid, {})
        return f"[Figure {order[fid]}. {meta.get('title', '')}. {meta.get('description', '')}]"

    text = FIG.sub(fig, md)
    return re.sub(r"\b(Fig(?:ure|\.)?)\s+([A-Z]\d+)\b",
                  lambda m: f"{m.group(1)} {order[m.group(2)]}" if m.group(2) in order else m.group(0), text)


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


def _artifact_data_text(m: dict, root: Path, max_rows: int = 80, max_chars: int = 6000) -> str:
    """A small table in full (CSV) or a JSON artifact's data, so a reviewer can check the numbers taken from it."""
    path = root / "artifacts" / m["id"] / m.get("file", "")
    try:
        if m["kind"] == "table" and path.suffix == ".parquet":
            import pandas as pd
            df = pd.read_parquet(path)
            if len(df) > max_rows:
                return ""
            text = df.to_csv(index=False, float_format="%.6g")
        elif m["kind"] == "json" and path.suffix == ".json":
            text = path.read_text(encoding="utf8")
        else:
            return ""
    except Exception:  # noqa: BLE001 (unreadable data: the summary still describes it)
        return ""
    return text if len(text) <= max_chars else text[:max_chars] + "\n... [data truncated]"


def evidence_text(artifacts: dict[str, dict], root: Path, cited: set[str] | None = None,
                  limit: int = 150000) -> str:
    """Input for the report reviewer. First every finding in full, then every artifact the report cites (with its
    summary, and its data when the table is small), then one line for each other artifact. Cited evidence comes
    first, so the other artifacts of a long run cannot push it past the limit."""
    cited = cited or set()
    findings, cited_parts, others = [], [], []
    for aid, m in artifacts.items():
        if m["kind"] == "finding":
            try:
                data = json.loads((root / "artifacts" / aid / "data.json").read_text())
                findings.append(f"{aid} (finding) {data.get('text')} | value: "
                                f"{json.dumps(data.get('value'), default=str)[:800]}")
            except (OSError, json.JSONDecodeError):
                findings.append(f"{aid} (finding) {m['title']}")
        elif aid in cited:
            short = (m["summary"] if isinstance(m["summary"], str) else m["summary"].get("text", ""))[:1200]
            status = f" [{m.get('status')}]" if m["kind"] in ("figure", "viz") else ""
            data = _artifact_data_text(m, root)
            cited_parts.append(f"{aid} ({m['kind']}{status}) {m['title']}: {m.get('description', '')[:800]}\n{short}"
                               + (f"\nDATA:\n{data}" if data else ""))
        else:
            others.append(f"{aid} ({m['kind']}) {m['title']}")
    text = "\n\n".join([*findings, *cited_parts]) + "\n\nOTHER ARTIFACTS (not cited):\n" + "\n".join(others)
    return text if len(text) <= limit else text[:limit] + "\n... [evidence truncated]"


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]


def run_record(root: Path) -> str:
    """The run's own record, from the harness's files (event log, usage files, cell log, artifacts), as Markdown.
    It is added to the report when the run is exported; the agents do not write it."""
    ev = _jsonl(root / "events.jsonl")
    starts = [e["ts"] for e in ev if e["agent"] == "user" and e["kind"] == "message"
              and not e["payload"].get("answer_to")]
    if not starts:
        return ""
    bounds = [*starts, float("inf")]
    rows, by_agent, models = [], {}, set()
    for i, t0 in enumerate(starts):
        seg = [e for e in ev if t0 <= e["ts"] < bounds[i + 1]]
        done = [e["payload"].get("seconds") for e in seg if e["kind"] == "done"]
        secs = done[-1] if done else seg[-1]["ts"] - t0
        costs = [e for e in seg if e["kind"] == "cost"]
        for e in costs:
            by_agent.setdefault(e["agent"], Counter())[i] += e["payload"].get("usd", 0.0)
            models.add(e["payload"].get("model", "?"))
        archived = root / "history" / f"turn{i + 1}" / "external_usage.json"
        current = root / "external_usage.json"
        ufile = archived if archived.exists() else (current if i == len(starts) - 1 else None)
        usage = json.loads(ufile.read_text()) if ufile is not None and ufile.exists() else {}
        jobs = [e["payload"] for e in seg if e["kind"] == "job" and e["payload"].get("action") == "end"]
        gates = [e["payload"] for e in seg if e["kind"] == "gate"]
        fig = [g for g in gates if g.get("artifact") != "report"]
        rep_ = [g for g in gates if g.get("artifact") == "report"]
        started = sum(1 for e in seg if e["kind"] == "job" and e["payload"].get("action") == "start")
        jobs_text = f"{started} started, {sum(1 for j in jobs if j.get('returncode') == 0)} succeeded" if started else "0"
        fig_text = f"{len(fig)}, {sum(g.get('verdict') == 'pass' for g in fig)} passed" if fig else "0"
        rep_text = f"{len(rep_)}: {', '.join(g.get('verdict', '?') for g in rep_)}" if rep_ else "0"
        rows.append(
            f"| {i + 1} | {datetime.fromtimestamp(t0, timezone.utc):%Y-%m-%d %H:%M} | {secs / 60:.0f} min | "
            f"{len(costs)} | ${sum(e['payload'].get('usd', 0.0) for e in costs):.2f} | "
            f"{usage.get('requests', 0):,} | ${usage.get('usd', 0.0):.2f} | {jobs_text} | {fig_text} | {rep_text} |")
    n = len(starts)
    agent_rows = [f"| {a} | " + " | ".join(f"${c[i]:.2f}" for i in range(n)) + f" | ${sum(c.values()):.2f} |"
                  for a, c in sorted(by_agent.items(), key=lambda kv: -sum(kv[1].values()))]
    total = sum(sum(c.values()) for c in by_agent.values())
    cells = _jsonl(root / "kernel_log.jsonl")
    per_agent = Counter(c["agent"] for c in cells)
    failed = Counter(c["agent"] for c in cells if not c["ok"])
    metas = [json.loads(p.read_text()) for p in sorted((root / "artifacts").glob("*/meta.json"))]
    figs = [m for m in metas if m["kind"] == "figure"]
    status = Counter(m.get("status") for m in figs)
    kinds = Counter(m["kind"] for m in metas if m["kind"] != "figure")
    report_status = root / "report" / "status.json"
    rs = json.loads(report_status.read_text()) if report_status.exists() else {}
    return "\n".join([
        "## Appendix: run record",
        "",
        "Generated by the harness from the run's event log, usage files, cell log and artifact store when the "
        "run was exported. The agents did not write this section. A turn is one instruction from the user to the "
        f"lead agent; this run had {n}. Model: {', '.join(sorted(models)) or 'unknown'}.",
        "",
        "| Turn | Started (UTC) | Wall time | LLM calls | LLM spend | API requests | API spend | Background jobs "
        "| Figure reviews | Report reviews |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        "LLM spend by agent (the critic does the independent figure and report reviews):",
        "",
        "| Agent | " + " | ".join(f"Turn {i + 1}" for i in range(n)) + " | Total |",
        "|---|" + "---|" * (n + 1),
        *agent_rows,
        "| all | " + " | ".join(f"${sum(c[i] for c in by_agent.values()):.2f}" for i in range(n))
        + f" | ${total:.2f} |",
        "",
        " ".join(part for part in [
            f"Code cells run by the agents (background jobs included): {len(cells)} "
            f"({', '.join(f'{a} {k}' for a, k in per_agent.most_common())}), of which {sum(failed.values())} "
            "failed (an agent reads the error and runs a corrected cell)." if cells else "",
            f"Artifacts: {', '.join(f'{v} {k}' for k, v in sorted(kinds.items()))}." if kinds else "",
            f"Figure versions submitted to the figure gate: {len(figs)} "
            f"({', '.join(f'{v} {k}' for k, v in sorted(status.items(), key=lambda kv: str(kv[0])))})."
            if figs else "",
            (f"Report gate: {rs.get('status')} in round {rs.get('round')}"
             + (f", with {len(rs['open_reader_points'])} wording points from the reader left open (review log)."
                if rs.get("open_reader_points") else ".")) if rs else ""] if part),
        "",
    ])
