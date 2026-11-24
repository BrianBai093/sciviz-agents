"""Export a finished report-mode run as a self-contained reproduction package (PLAN_P2 §6).

<out>/
  report.pdf, report.md, report.html      the report as released by the report gate
  figures/                                approved figures (latest version per slug), PDF + PNG
  data/artifacts/<id>/                    every data artifact (meta.json + parquet/json)
  data/api_responses.sqlite               the frozen external API responses this run used
  scripts/cells/NNNN_<agent>.py           every code cell the agents ran, in order (jobs included)
  scripts/cells.jsonl                     cell index: order, agent, original success, artifacts created
  scripts/run_all.py                      offline replay of all cells + comparison with the original artifacts
  trace/                                  claim plan, decisions, events, reviews, usage, lead report
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .openalex import export_cache_subset

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
        import shutil
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "inputs").mkdir()
    for f in (PKG / "trace" / "inputs").glob("*"):
        (work / "inputs" / f.name).write_bytes(f.read_bytes())
    svc = OpenAlexService("", PKG / "data" / "api_responses.sqlite", budget_usd=0, offline=True)
    url = svc.start_proxy()
    os.environ.update({"SCIVIZ_WORKSPACE": str(work), "SCIVIZ_DB": args.db, "SCIVIZ_OPENALEX_URL": url,
                       "MPLBACKEND": "Agg"})
    os.chdir(work)
    logs = work / "_cell_logs"
    logs.mkdir()
    cells = [json.loads(line) for line in (HERE / "cells.jsonl").read_text().splitlines() if line.strip()]
    spaces, problems = {}, []
    t0 = time.time()
    for c in cells:
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
        if ok != c["ok"]:
            problems.append(f"cell {c['file']}: original {'ok' if c['ok'] else 'failed'}, replay {'ok' if ok else 'failed'}")
        print(f"{c['file']}: {'ok' if ok else 'failed'}{'' if ok == c['ok'] else '  <-- differs from the original run'}",
              flush=True)
    svc.close()
    same, diff, missing = [], [], []
    for meta_file in sorted((PKG / "data" / "artifacts").glob("*/meta.json")):
        aid = meta_file.parent.name
        meta = json.loads(meta_file.read_text())
        new = work / "artifacts" / aid / meta["file"]
        old = meta_file.parent / meta["file"]
        if not new.exists():
            missing.append(aid)
            continue
        if meta["kind"] == "table":
            a, b = pd.read_parquet(old), pd.read_parquet(new)
            try:
                pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-9, check_dtype=False)
                same.append(aid)
            except AssertionError:
                diff.append(aid)
        else:
            (same if json.loads(old.read_text()) == json.loads(new.read_text()) else diff).append(aid)
    print(f"\nReplayed {len(cells)} cells in {time.time() - t0:.0f}s. Artifacts identical: {len(same)}; "
          f"different: {len(diff)} {diff}; not recreated: {len(missing)} {missing}")
    for p in problems:
        print("  " + p)
    print("Differences are expected for artifacts that record timings or live usage counters (see their titles).")


if __name__ == "__main__":
    sys.exit(main())
'''


def export_run(ws_root: Path, out: Path, cache_src: Path) -> dict:
    ws_root, out = Path(ws_root), Path(out)
    if out.exists():
        shutil.rmtree(out)
    (out / "figures").mkdir(parents=True)
    (out / "data" / "artifacts").mkdir(parents=True)
    (out / "scripts" / "cells").mkdir(parents=True)
    (out / "trace" / "inputs").mkdir(parents=True)
    summary: dict = {"figures": [], "artifacts": 0, "cells": 0, "api_responses": 0}

    rep = ws_root / "report"
    for name in ("report.pdf", "report.md", "report.html", "reviews.jsonl", "status.json"):
        if (rep / name).exists():
            shutil.copy(rep / name, (out / name) if name.startswith("report.") else (out / "trace" / name))

    metas = [json.loads(p.read_text()) for p in sorted((ws_root / "artifacts").glob("*/meta.json"))]
    latest: dict[str, dict] = {}
    for m in metas:
        if m["kind"] == "figure" and m.get("status") in ("approved", "approved_with_issues"):
            if m["slug"] not in latest or m["version"] > latest[m["slug"]]["version"]:
                latest[m["slug"]] = m
    for slug, m in sorted(latest.items(), key=lambda kv: int(kv[1]["id"][1:])):
        src = ws_root / "artifacts" / m["id"]
        shutil.copy(src / "figure.pdf", out / "figures" / f"{m['id']}_{slug}.pdf")
        shutil.copy(src / "figure.png", out / "figures" / f"{m['id']}_{slug}.png")
        summary["figures"].append(f"{m['id']}_{slug}")
    for m in metas:
        if m["kind"] in ("viz", "figure"):
            continue
        d = out / "data" / "artifacts" / m["id"]
        d.mkdir()
        shutil.copy(ws_root / "artifacts" / m["id"] / "meta.json", d / "meta.json")
        shutil.copy(ws_root / "artifacts" / m["id"] / m["file"], d / m["file"])
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
        index.append({"n": n, "file": fname, "agent": c["agent"], "ok": c["ok"], "created": c["created"],
                      "job": c.get("job")})
    (out / "scripts" / "cells.jsonl").write_text("".join(json.dumps(x) + "\n" for x in index))
    (out / "scripts" / "run_all.py").write_text(RUN_ALL, encoding="utf8")
    summary["cells"] = len(index)

    keys_file = ws_root / "external_keys.json"
    if keys_file.exists() and cache_src.exists():
        summary["api_responses"] = export_cache_subset(cache_src, out / "data" / "api_responses.sqlite",
                                                       set(json.loads(keys_file.read_text())))
    for name in ("claim_plan.json", "decisions.jsonl", "events.jsonl", "external_usage.json", "lead_report.md",
                 "kernel_log.jsonl"):
        if (ws_root / name).exists():
            shutil.copy(ws_root / name, out / "trace" / name)
    for f in (ws_root / "inputs").glob("*"):
        shutil.copy(f, out / "trace" / "inputs" / f.name)
    reviews = {m["id"]: m.get("reviews", []) for m in metas if m["kind"] == "figure"}
    (out / "trace" / "figure_reviews.json").write_text(json.dumps(reviews, indent=1))
    (out / "export_summary.json").write_text(json.dumps(summary, indent=1))
    return summary
