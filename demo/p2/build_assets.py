"""Data for the Project 2 demo slides, taken from the exported reproduction package.

    uv run python demo/p2/build_assets.py [--replay-log logs/p2_replay4.log]

Writes demo/p2/slides/trace_data.js (the run's event log, condensed into the lines a terminal would show, with running
counters) and, when a replay log is given, demo/p2/slides/replay_data.js (the output of scripts/run_all.py).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVENTS = REPO / "reproductions" / "wu2019" / "trace" / "events.jsonl"
STAGES = ["stage 1 · full run on 8,000 works", "stage 2 · two corrections, then the report",
          "stage 3 · plain-language rewrite", "stage 3 · continued", "stage 3 · three sentences",
          "stage 3 · open review points"]


def cut(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def goal(brief: str) -> str:
    for line in brief.splitlines():
        if line.startswith("GOAL:"):
            return line[5:].strip()
    return brief


def trace() -> dict:
    ev = [json.loads(line) for line in EVENTS.read_text(encoding="utf8").splitlines() if line.strip()]
    rows: list[dict] = [{"line": "── pilot · 100 works, separate session: designs and prices the data collection ──",
                         "cls": "turn", "stage": "pilot · 100 works"}]
    turn, t_turn, agent_min, usd, figs, figs_ok, reports = -1, 0.0, 0.0, 0.0, 0, 0, 0
    req_done, req_turn = 0, 0  # API requests of finished turns, and of the current one (each turn counts from 0)
    stage = "pilot · 100 works"
    for e in ev:
        a, k, p = e["agent"], e["kind"], e["payload"] or {}
        line, cls = None, a
        if k == "message" and a == "user" and not p.get("answer_to"):
            if turn >= 0:
                agent_min += (last_ts - t_turn) / 60
            req_done, req_turn = req_done + req_turn, 0
            turn += 1
            t_turn = e["ts"]
            stage = STAGES[turn] if turn < len(STAGES) else f"turn {turn + 1}"
            line, cls = f"── turn {turn + 1} · {stage} ──", "turn"
        elif k == "delegate":
            line = f"lead → {p.get('to')}: {cut(goal(p.get('brief', '')), 96)}"
        elif k == "tool_call":
            tool, args = p.get("tool"), p.get("args") or {}
            if tool == "run_python":
                first = next((ln for ln in str(args.get("code", "")).splitlines() if ln.strip()), "")
                line, cls = f"{a} ▸ python: {cut(first, 80)}", a
            elif tool == "inspect_artifact":
                line, cls = f"{a} reads {args.get('artifact_id')}", "dim"
            elif tool == "write_section":
                line = f"{a} writes section “{args.get('name')}”"
            elif tool == "remove_section":
                line = f"{a} removes section “{args.get('name')}”"
            elif tool == "submit_figure":
                line = f"{a} submits figure “{cut(args.get('title', ''), 70)}”"
            elif tool == "submit_report":
                line = f"{a} submits the report: “{cut(args.get('title', ''), 70)}”"
            elif tool in ("openalex_query", "run_sql", "list_tables", "describe_table", "read_input"):
                line, cls = f"{a} ▸ {tool} {cut(json.dumps(args), 60)}", "dim"
        elif k == "artifact":
            line, cls = f"{a} saves {p.get('id')} · {cut(p.get('title', ''), 80)}", "dim"
        elif k == "job":
            if p.get("action") == "start":
                line, cls = f"{a} starts background job “{cut(p.get('name', ''), 60)}”", "job"
            else:
                line, cls = f"background job {p.get('job')} ended", "job"
        elif k == "gate":
            what = "report" if p.get("artifact") == "report" else f"figure {p.get('artifact')}"
            ok = p.get("verdict") == "pass"
            if p.get("artifact") == "report":
                reports += 1
            else:
                figs += 1
                figs_ok += ok
            if p.get("artifact") == "report":  # two checks: show their scores, not one reviewer's summary
                sc = p.get("scores") or {}
                detail = ", ".join(f"{k} {v}" for k, v in sc.items())
            else:
                detail = cut(p.get("summary", ""), 80)
            line, cls = f"critic: {what} {'passed' if ok else 'sent back'} — {detail}", "pass" if ok else "fail"
        elif k == "report" and a == "writer":
            line, cls = f"report released ({p.get('status')})", "pass"
        elif k == "external_usage":
            req_turn, cls = max(req_turn, p.get("requests", 0)), "dim"
            line = f"OpenAlex API: {req_done + req_turn:,} requests so far"
        elif k == "cost":
            usd += p.get("usd", 0.0)
        elif k == "done":
            line, cls = f"turn finished · {p.get('seconds', 0) / 60:.0f} min", "turn"
        last_ts = e["ts"]
        if line:
            rows.append({"line": line, "cls": cls, "stage": stage, "min": round(agent_min + (e["ts"] - t_turn) / 60, 1)
                         if turn >= 0 else 0, "usd": round(usd, 2), "req": req_done + req_turn, "figs": figs, "figs_ok": figs_ok,
                         "reports": reports})
    return {"rows": rows}


def replay(log: Path) -> dict:
    """The replay's per-cell lines. A failed cell is labelled: most also failed in the original run (the agent read
    the error and ran a corrected cell); the others fail offline by design (REPRODUCE.md)."""
    cells = REPO / "reproductions" / "wu2019" / "scripts" / "cells.jsonl"
    ok_then = {c["file"]: c["ok"] for c in map(json.loads, cells.read_text().splitlines())}
    out = []
    for ln in (x.rstrip() for x in log.read_text(encoding="utf8").splitlines()):
        if ln.endswith(": ok") or ln.startswith("Unpack"):
            out.append(ln)
        elif ": failed" in ln and not ln.startswith(" "):
            name = ln.split(": failed")[0]
            out.append(f"{name}: failed, as in the original run" if not ok_then.get(name, True)
                       else f"{name}: fails offline by design")
    return {"lines": out}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay-log", type=Path)
    a = ap.parse_args()
    out = HERE / "slides"
    data = trace()
    (out / "trace_data.js").write_text("const TRACE = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf8")
    print(f"trace: {len(data['rows'])} lines")
    if a.replay_log:
        r = replay(a.replay_log)
        (out / "replay_data.js").write_text("const REPLAY = " + json.dumps(r, ensure_ascii=False) + ";\n",
                                            encoding="utf8")
        print(f"replay: {len(r['lines'])} lines")
