"""Export a finished report-mode run as a self-contained reproduction package (PLAN_P2 §6).

<out>/
  report.pdf, report.md, report.html      the report released by the report gate, with the harness's reproduction
                                          instructions and run record
  figures/                                the report's figures (figure<n>_<id>_<slug>), PDF + PNG; figures/other/:
                                          every other figure that passed the figure gate
  data/artifacts/<id>/                    every artifact except interactive views (meta.json + parquet/json/figure)
  data/api_responses.sqlite.xz            the frozen external API responses this run used (xz; run_all.py unpacks it)
  scripts/cells/NNNN_<agent>.py           every code cell the agents ran, in order (jobs included)
  scripts/cells.jsonl                     cell index: order, agent, original success, artifacts created
  scripts/jobs.jsonl                      background jobs: id, start time, folder under trace/jobs/
  scripts/files/, scripts/files.jsonl     files the agents wrote with their file tools (content after each write)
  scripts/run_all.py                      offline replay of all cells + comparison with the original artifacts
  trace/                                  claim plan, decisions, events, reviews, usage, lead report
"""
from __future__ import annotations

import html
import json
import lzma
import re
import shutil
from pathlib import Path

from .openalex import export_cache_subset
from .report import FIG, render_pdf, run_record, to_html

RUN_ALL = r'''"""Replay every code cell of this run, in order, offline, and compare the results with the original artifacts.

  uv run python reproductions/<run>/scripts/run_all.py [--workdir DIR]

Needs the repository environment (`uv sync`) and the snapshot database (README §1). External API calls are served
from data/api_responses.sqlite, the frozen responses this run used: no key and no network access are needed. Each
cell runs with the same helpers the agents had (sql, load, save_table, openalex, ...); a background job's cell runs
in a fresh namespace, as it did in its own process. Artifacts get their original ids so later cells find them.
"""
import argparse
import contextlib
import io
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = next((p for p in [PKG, *PKG.parents] if (p / "pyproject.toml").exists()), Path.cwd())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=str(PKG / "replay"))
    ap.add_argument("--db", default=os.getenv("SCIVIZ_DB", str(REPO / "data" / "columbia.duckdb")))
    args = ap.parse_args()
    import pandas as pd
    from sciviz.harness.openalex import OpenAlexService
    from sciviz.harness.workspace import Workspace
    from sciviz.tools.python_exec import PRELUDE

    work = Path(args.workdir)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.copytree(PKG / "trace" / "inputs", work / "inputs")
    if (PKG / "trace" / "kernel_log.jsonl").exists():  # the harness's cell log (cells may read it)
        shutil.copy(PKG / "trace" / "kernel_log.jsonl", work / "kernel_log.jsonl")
    cache = PKG / "data" / "api_responses.sqlite"
    if not cache.exists() and cache.with_suffix(".sqlite.xz").exists():
        import lzma
        print("Unpacking data/api_responses.sqlite.xz ...", flush=True)
        with lzma.open(cache.with_suffix(".sqlite.xz")) as src, cache.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    if not cache.exists():
        print("data/api_responses.sqlite is missing: cells that call the external API will fail, and the artifacts "
              "they made are taken from the original run.", flush=True)
    svc = OpenAlexService("", PKG / "data" / "api_responses.sqlite", budget_usd=0, offline=True)
    url = svc.start_proxy()
    os.environ.update({"SCIVIZ_WORKSPACE": str(work), "SCIVIZ_DB": args.db, "SCIVIZ_OPENALEX_URL": url,
                       "MPLBACKEND": "Agg"})
    os.chdir(work)
    logs = work / "_cell_logs"
    logs.mkdir()
    cells = [json.loads(line) for line in (HERE / "cells.jsonl").read_text().splitlines() if line.strip()]
    jobs = [json.loads(line) for line in (HERE / "jobs.jsonl").read_text().splitlines() if line.strip()]
    files = [json.loads(line) for line in (HERE / "files.jsonl").read_text().splitlines() if line.strip()]
    # In time order: the files agents wrote with their file tools; the files the harness wrote when a background
    # job started (script, log, metadata under jobs/<id>/); and the cells, which may read or run those files.
    # Figures are registered by the figure gate (a tool, not a cell); later cells may read them.
    figures = [m for m in (json.loads(p.read_text()) for p in (PKG / "data" / "artifacts").glob("*/meta.json"))
               if m["kind"] == "figure"]
    timeline = sorted([(f["ts"], 0, "file", f) for f in files] + [(j["started"], 0, "job", j) for j in jobs]
                      + [(m["created_at"], 0, "figure", m) for m in figures]
                      + [(c["ts"], 1, "cell", c) for c in cells], key=lambda x: x[:2])
    spaces, problems, restored = {}, [], []
    t0 = time.time()
    for _, _, what, c in timeline:
        if what == "job":
            shutil.copytree(PKG / "trace" / "jobs" / c["dir"], work / "jobs" / c["id"], dirs_exist_ok=True)
            continue
        if what == "figure":
            shutil.copytree(PKG / "data" / "artifacts" / c["id"], work / "artifacts" / c["id"], dirs_exist_ok=True)
            continue
        if what == "file":
            if c.get("file") is None:
                print(f"file write {c['path']}: content unknown, not restored", flush=True)
                continue
            target = work / c["path"].lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((HERE / "files" / c["file"]).read_bytes())
            continue
        if c.get("stopped"):  # a job that was stopped before it ended is not run again
            print(f"{c['file']}: skipped (job stopped in the original run)", flush=True)
            continue
        key = f"job:{c['n']}" if c.get("job") else c["agent"]
        if key not in spaces:
            os.environ["SCIVIZ_AGENT"] = c["agent"]
            ns = {"__name__": f"cell_{c['agent']}"}
            exec(PRELUDE, ns)
            spaces[key] = ns
        ns = spaces[key]
        expected = list(c["created"])

        def next_id(prefix, _expected=expected, _ws=ns["_ws"], _orig=Workspace._next_id):
            if _expected and _expected[0].rstrip("0123456789") == prefix:
                return _expected.pop(0)
            return _orig(_ws, prefix + "x")  # unexpected extra artifact: never reuse an original id

        ns["_ws"]._next_id = next_id
        code = (HERE / "cells" / c["file"]).read_text(encoding="utf8")
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                exec(compile(code, c["file"], "exec"), ns)
            ok = True
        except BaseException:  # noqa: BLE001 (replay must continue; original failures are expected)
            out.write("\n" + traceback.format_exc())
            ok = False
        (logs / (c["file"] + ".txt")).write_text(out.getvalue(), encoding="utf8")
        note = ""
        if ok != c["ok"]:
            problems.append(f"cell {c['file']}: original {'ok' if c['ok'] else 'failed'}, replay {'ok' if ok else 'failed'}")
            note = "  <-- differs from the original run"
        if c["ok"] and not ok:  # continue with the artifacts this cell made in the original run
            for aid in c["created"]:
                if (PKG / "data" / "artifacts" / aid).exists() and not (work / "artifacts" / aid).exists():
                    shutil.copytree(PKG / "data" / "artifacts" / aid, work / "artifacts" / aid)
                    restored.append(aid)
            note += f"; its artifacts were taken from the original run ({', '.join(c['created']) or 'none'})"
        print(f"{c['file']}: {'ok' if ok else 'failed'}{note}", flush=True)
    svc.close()
    def frames_equal(a, b):
        try:
            pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True), check_exact=False,
                                          rtol=1e-9, check_dtype=False)
            return True
        except (AssertionError, TypeError, ValueError):
            return False

    def by_rows(df):  # rows in a canonical order (parallel requests may have returned them in another order)
        return df.sort_values(list(df.columns), na_position="first", kind="stable")

    same, reordered, diff, missing, outside = [], [], [], [], []
    for meta_file in sorted((PKG / "data" / "artifacts").glob("*/meta.json")):
        aid = meta_file.parent.name
        meta = json.loads(meta_file.read_text())
        if aid in restored or meta["kind"] == "figure":  # figures come from the figure gate, not from cells
            continue
        new = work / "artifacts" / aid / meta["file"]
        old = meta_file.parent / meta["file"]
        if not new.exists():
            (missing if meta.get("code") else outside).append(aid)
            continue
        if meta["kind"] == "table":
            a, b = pd.read_parquet(old), pd.read_parquet(new)
            if frames_equal(a, b):
                same.append(aid)
            else:
                try:
                    equal_rows = frames_equal(by_rows(a), by_rows(b))
                except TypeError:  # columns that cannot be sorted
                    equal_rows = False
                (reordered if equal_rows else diff).append(aid)
        else:
            (same if json.loads(old.read_text()) == json.loads(new.read_text()) else diff).append(aid)
    print(f"\nReplayed {len(cells)} cells in {time.time() - t0:.0f}s. Artifacts recomputed and identical: {len(same)}; "
          f"identical up to row order: {len(reordered)} {reordered}; recomputed and different: {len(diff)} {diff}; "
          f"taken from the original run: {len(restored)} {restored}; not recreated: {len(missing)} {missing}; "
          f"made outside any recorded cell (for example by a job stopped before it ended): {len(outside)} {outside}")
    # Figures: the newest gated version of each figure against the file the replay rendered for it.
    from PIL import Image, ImageChops
    newest = {}
    for m in figures:
        if m["slug"] not in newest or int(m["id"][1:]) > int(newest[m["slug"]]["id"][1:]):
            newest[m["slug"]] = m
    rendered = sorted((work / "figures").glob("*.png")) if (work / "figures").exists() else []

    def same_pixels(a_path, b_path):
        a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
        return a.size == b.size and ImageChops.difference(a, b).getbbox() is None

    fig_same, fig_diff = [], []
    for slug, m in sorted(newest.items()):
        gated = PKG / "data" / "artifacts" / m["id"] / "figure.png"
        # the file submitted under this slug may have been renamed or rendered under another name later
        order = sorted(rendered, key=lambda f: f.stem != slug)
        (fig_same if any(same_pixels(gated, f) for f in order) else fig_diff).append(m["id"])
    print(f"Newest gated version of each figure, compared with the PNG files the replay rendered: identical pixels "
          f"{len(fig_same)} {fig_same}; no identical rendering {len(fig_diff)} {fig_diff}")
    for p in problems:
        print("  " + p)
    print("Expected differences: artifacts that record timings, retries or live API usage, and results of cells that "
          "checked them (see the titles and the cell logs in the replay folder's _cell_logs/).")
    (work / "replay_summary.json").write_text(json.dumps({
        "cells": len(cells), "identical": same, "identical_up_to_row_order": reordered, "different": diff,
        "restored": restored, "missing": missing, "outside_cells": outside, "figures_identical": fig_same,
        "figures_different": fig_diff, "problems": problems}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
'''


GENERATED = ("report.pdf", "report.md", "report.html", "figures", "data", "scripts", "trace", "export_summary.json",
             "replay")


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]


def _job_instances(ws_root: Path) -> list[dict]:
    """Every background job of the run, with its folder: jobs/<id>/, and history/turnN/jobs/<id>/ for jobs of
    earlier turns whose folders were later reused (sessions before job ids were unique across turns)."""
    seen, found = set(), []
    for d in [*sorted((ws_root / "history").glob("turn*/jobs/*")), *sorted((ws_root / "jobs").glob("*"))]:
        if (d / "job.json").exists():
            meta = json.loads((d / "job.json").read_text())
            key = (meta["id"], round(meta["started"], 3))
            if key not in seen:
                seen.add(key)
                found.append({"id": meta["id"], "started": round(meta["started"], 3), "src": d})
    return sorted(found, key=lambda j: j["started"])


def _reproduce_note(ws_root: Path, out: Path) -> str:
    """Plain instructions for checking the report. The harness writes them, since it builds the package."""
    try:
        rel = out.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        rel = out.as_posix()
    cells = len(_jsonl(ws_root / "kernel_log.jsonl"))
    rows = [
        "| `report.pdf`, `figures/` | this report, and its figures as PDF and PNG files |",
        ("| `data/artifacts/<id>/` | every saved result the report cites (the ids in square brackets), with the code "
         "that made it and its inputs |"),
        *(["| `data/api_responses.sqlite.xz` | the responses of the external data service that the run used, frozen |"]
          if (ws_root / "external_keys.json").exists() else []),
        f"| `scripts/` | the {cells} code steps the agents ran, in order, and `run_all.py` |",
        "| `trace/` | the run's inputs, plan, decisions, reviews and logs |",
    ]
    rerun = (f"To rerun the whole analysis offline, without API keys or network access, run "
             f"`uv run python {rel}/scripts/run_all.py` from the repository. It repeats every code step on the frozen "
             f"data and compares each result with the original.")
    if (out / "REPRODUCE.md").exists():
        rerun += " `REPRODUCE.md` in the package gives the full instructions."
    return "\n".join([
        "## How to reproduce this report",
        "",
        ("Added by the harness when the run was exported. A team of AI agents (a lead, a data agent, an analysis "
         "agent and a writer) produced this report, and independent reviewers checked each figure and the text "
         "before release. Everything needed to check the report is in the package that contains it:"),
        "",
        "| Path | Contents |",
        "|---|---|",
        *rows,
        "",
        rerun,
        "",
    ])


def _export_report(ws_root: Path, out: Path, arts: dict[str, dict]) -> list[str]:
    """The report as the report gate released it, plus the harness's reproduction instructions and run record,
    rendered again with its figures in figures/ (figure<n>_<id>_<slug>.pdf/png, numbered as in the report), so the
    HTML works inside the package.
    The released Markdown is kept in trace/report_released.md. Returns the ids of the figures the report places."""
    rep = ws_root / "report"
    shutil.copy(rep / "report.md", out / "trace" / "report_released.md")
    md = "\n\n".join([(rep / "report.md").read_text(encoding="utf8").rstrip(), _reproduce_note(ws_root, out),
                       run_record(ws_root)])
    placed = list(dict.fromkeys(FIG.findall(md)))
    names = {fid: f"figure{n}_{fid}_{arts[fid]['slug']}" for n, fid in enumerate(placed, 1)}
    for fid, name in names.items():
        for ext in ("pdf", "png"):
            shutil.copy(ws_root / "artifacts" / fid / f"figure.{ext}", out / "figures" / f"{name}.{ext}")
    status = json.loads((rep / "status.json").read_text()) if (rep / "status.json").exists() else {}
    subtitle = status.get("subtitle")
    if subtitle is None and (rep / "report.html").exists():  # runs before the subtitle was kept in status.json
        found = re.search(r'<div class="subtitle">(.*?)</div>', (rep / "report.html").read_text(encoding="utf8"), re.S)
        subtitle = html.unescape(found.group(1)) if found else ""
    (out / "report.md").write_text(md, encoding="utf8")
    page = to_html(md, arts, ws_root, subtitle or "", img_src=lambda fid: f"figures/{names[fid]}.png")
    render_pdf(page, out / "report.html", out / "report.pdf")
    return placed


def export_run(ws_root: Path, out: Path, cache_src: Path) -> dict:
    ws_root, out = Path(ws_root), Path(out)
    for name in GENERATED:  # replace what an earlier export wrote; keep hand-written files such as REPRODUCE.md
        target = out / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    (out / "figures").mkdir(parents=True)
    (out / "data" / "artifacts").mkdir(parents=True)
    (out / "scripts" / "cells").mkdir(parents=True)
    (out / "trace" / "inputs").mkdir(parents=True)
    summary: dict = {"figures": [], "artifacts": 0, "cells": 0, "api_responses": 0}

    rep = ws_root / "report"
    for name in ("reviews.jsonl", "status.json"):
        if (rep / name).exists():
            shutil.copy(rep / name, out / "trace" / name)

    metas = [json.loads(p.read_text()) for p in sorted((ws_root / "artifacts").glob("*/meta.json"))]
    arts = {m["id"]: m for m in metas}
    placed = _export_report(ws_root, out, arts) if (rep / "report.md").exists() else []
    others = [m for m in sorted(metas, key=lambda m: int(m["id"][1:]) if m["id"][1:].isdigit() else 0)
              if m["kind"] == "figure" and m.get("status") in ("approved", "approved_with_issues")
              and m["id"] not in placed]
    for m in others:  # approved figures the report does not show (for example earlier versions)
        d = out / "figures" / ("other" if placed else "")
        d.mkdir(parents=True, exist_ok=True)
        for ext in ("pdf", "png"):
            shutil.copy(ws_root / "artifacts" / m["id"] / f"figure.{ext}", d / f"{m['id']}_{m['slug']}.{ext}")
    summary["figures"] = [f"figure {n}: {fid}" for n, fid in enumerate(placed, 1)] + [m["id"] for m in others]
    for m in metas:
        if m["kind"] == "viz":
            continue
        d = out / "data" / "artifacts" / m["id"]
        d.mkdir()
        for name in ("meta.json", m["file"], *(("figure.pdf",) if m["kind"] == "figure" else ())):
            shutil.copy(ws_root / "artifacts" / m["id"] / name, d / name)
        summary["artifacts"] += 1

    log = ws_root / "kernel_log.jsonl"
    cells = [json.loads(line) for line in log.read_text().splitlines() if line.strip()] if log.exists() else []
    cells.sort(key=lambda c: c["ts"])
    index = []
    for n, c in enumerate(cells, 1):
        fname = f"{n:04d}_{c['agent']}{'_' + c['job'] if c.get('job') else ''}.py"
        header = (f"# cell {n} | agent: {c['agent']}{' | background job ' + c['job'] if c.get('job') else ''} | "
                  f"original run: {'ok' if c['ok'] else 'failed'} | artifacts created: {', '.join(c['created']) or 'none'}\n")
        (out / "scripts" / "cells" / fname).write_text(header + c["code"] + "\n", encoding="utf8")
        index.append({"n": n, "file": fname, "ts": c["ts"], "agent": c["agent"], "ok": c["ok"],
                      "created": c["created"], "job": c.get("job"), "stopped": c.get("stopped", False)})
    (out / "scripts" / "cells.jsonl").write_text("".join(json.dumps(x) + "\n" for x in index))
    (out / "scripts" / "run_all.py").write_text(RUN_ALL, encoding="utf8")
    summary["cells"] = len(index)

    keys_file = ws_root / "external_keys.json"
    if keys_file.exists() and cache_src.exists():
        db = out / "data" / "api_responses.sqlite"
        summary["api_responses"] = export_cache_subset(cache_src, db, set(json.loads(keys_file.read_text())))
        with db.open("rb") as src, lzma.open(db.with_suffix(".sqlite.xz"), "wb", preset=9) as dst:
            shutil.copyfileobj(src, dst)  # the package keeps the compressed copy; run_all.py unpacks it
        db.unlink()
    for name in ("claim_plan.json", "decisions.jsonl", "events.jsonl", "external_usage.json", "lead_report.md",
                 "kernel_log.jsonl"):
        if (ws_root / name).exists():
            shutil.copy(ws_root / name, out / "trace" / name)
    for f in (ws_root / "inputs").glob("*"):
        shutil.copy(f, out / "trace" / "inputs" / f.name)
    files_index = []
    for n, rec in enumerate(_jsonl(ws_root / "file_log.jsonl"), 1):
        name = None
        if rec.get("content") is not None:
            name = f"{n:04d}_{Path(rec['path']).name}"
            (out / "scripts" / "files").mkdir(exist_ok=True)
            (out / "scripts" / "files" / name).write_text(rec["content"], encoding="utf8")
        files_index.append({"ts": rec["ts"], "path": rec["path"], "op": rec["op"], "file": name,
                            **({"source": rec["source"]} if rec.get("source") else {})})
    (out / "scripts" / "files.jsonl").write_text("".join(json.dumps(x) + "\n" for x in files_index))
    summary["file_writes"] = len(files_index)
    jobs_index = []
    for j in _job_instances(ws_root):
        d = out / "trace" / "jobs" / f"{j['id']}_{int(j['started'])}"
        d.mkdir(parents=True)
        for name in ("script.py", "job.json", "log.txt"):
            if (j["src"] / name).exists():
                shutil.copy(j["src"] / name, d / name)
        jobs_index.append({"id": j["id"], "started": j["started"], "dir": d.name})
    (out / "scripts" / "jobs.jsonl").write_text("".join(json.dumps(x) + "\n" for x in jobs_index))
    summary["jobs"] = len(jobs_index)
    if (ws_root / "history").is_dir():  # earlier turns of a continued session: constraints, lead report, API usage
        shutil.copytree(ws_root / "history", out / "trace" / "history", ignore=shutil.ignore_patterns("jobs"))
    reviews = {m["id"]: m.get("reviews", []) for m in metas if m["kind"] == "figure"}
    (out / "trace" / "figure_reviews.json").write_text(json.dumps(reviews, indent=1))
    (out / "export_summary.json").write_text(json.dumps(summary, indent=1))
    return summary
