"""Replay every code cell of this run, in order, offline, and compare the results with the original artifacts.

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
