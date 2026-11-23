"""Run the evaluation tasks in multi-agent or single-agent mode and record outcomes (DECISIONS D13, D40).

  uv run python evals/run_eval.py --mode multi            # all tasks, in parallel
  uv run python evals/run_eval.py --mode single --tasks t4_flows

Per task: whether an approved view was shown, gate rounds (automated rejections, critic rejections, passes),
escalations, wall time, cost, model calls per agent, critic scores, and a screenshot of the shown view.
Results: evals/results/<mode>.json, evals/results/shots/, and evals/results/summary.md (both modes).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sciviz.runner import run_turn  # noqa: E402
from sciviz.session import Session  # noqa: E402

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def run_task(task: dict, mode: str, stamp: str) -> dict:
    s = Session(f"eval-{mode}-{task['id']}-{stamp}")
    t0 = time.time()
    error = None
    try:
        run_turn(s, task["question"], mode=mode)
    except Exception as e:  # recorded, the eval continues
        error = f"{type(e).__name__}: {e}"
    seconds = time.time() - t0
    evs = s.events.read_all()
    gates = [e["payload"] for e in evs if e["kind"] == "gate"]
    calls = Counter(e["agent"] for e in evs if e["kind"] == "cost")
    views = s.ws.views()["views"]
    shown = [v["viz"] for v in views]
    shot = None
    if shown:
        src = s.ws.artifact_dir(shown[-1]) / "shots" / "default.png"
        if src.exists():
            (RESULTS / "shots").mkdir(parents=True, exist_ok=True)
            shot = RESULTS / "shots" / f"{mode}_{task['id']}.png"
            shutil.copy(src, shot)
    approved = [m["id"] for m in s.ws.list() if m["kind"] == "viz" and m.get("status") in ("approved", "approved_with_issues")]
    final_critic = next((g for g in reversed(gates) if g.get("verdict") == "pass"), None)
    result = {
        "task": task["id"], "mode": mode, "session": s.id, "question": task["question"],
        "success": bool(shown) and error is None,
        "views_shown": shown, "approved": approved,
        "gate_automated_rejections": sum(1 for g in gates if g.get("stage") == "automated"),
        "gate_critic_rejections": sum(1 for g in gates if g.get("verdict") == "revise" and g.get("stage") != "automated"),
        "gate_passes": sum(1 for g in gates if g.get("verdict") == "pass"),
        "escalated": any(e["kind"] == "plan" and "escalat" in str(e["payload"].get("escalation", "")) for e in evs),
        "critic_scores": final_critic.get("scores") if final_critic else None,
        "seconds": round(seconds, 1), "cost_usd": round(s.ledger.session_total(s.id), 4),
        "model_calls": dict(calls), "libraries": [],
        "screenshot": str(shot.relative_to(ROOT.parent)) if shot else None, "error": error,
    }
    if shown:
        result["libraries"] = [f"{x['name']}@{x['version']}" for x in s.ws.load_manifest(shown[-1]).get("libraries", [])]
    s.close()
    print(json.dumps({k: result[k] for k in ("task", "mode", "success", "gate_passes", "gate_critic_rejections",
                                            "gate_automated_rejections", "seconds", "cost_usd")}), flush=True)
    return result


def summary_md() -> str:
    rows = []
    for mode in ("multi", "single"):
        p = RESULTS / f"{mode}.json"
        if p.exists():
            rows += json.loads(p.read_text())
    lines = ["| Task | Mode | Success | Gate rounds (pass / critic revise / auto revise) | Escalated | Time (s) | Cost ($) | Libraries |",
             "|---|---|---|---|---|---:|---:|---|"]
    for r in sorted(rows, key=lambda r: (r["task"], r["mode"])):
        lines.append(f"| {r['task']} | {r['mode']} | {'✅' if r['success'] else '❌'} | {r['gate_passes']} / "
                     f"{r['gate_critic_rejections']} / {r['gate_automated_rejections']} | {'yes' if r['escalated'] else 'no'} | "
                     f"{r['seconds']:.0f} | {r['cost_usd']:.2f} | {', '.join(r['libraries']) or 'none'} |")
    for mode in ("multi", "single"):
        rs = [r for r in rows if r["mode"] == mode]
        if rs:
            lines.append(f"| **all** | {mode} | {sum(r['success'] for r in rs)}/{len(rs)} | | | "
                         f"{sum(r['seconds'] for r in rs) / len(rs):.0f} avg | {sum(r['cost_usd'] for r in rs):.2f} total | |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["multi", "single"], required=True)
    ap.add_argument("--tasks", default="", help="comma-separated task ids (default: all)")
    ap.add_argument("--parallel", type=int, default=4)
    a = ap.parse_args()
    tasks = yaml.safe_load((ROOT / "tasks.yaml").read_text())
    if a.tasks:
        keep = set(a.tasks.split(","))
        tasks = [t for t in tasks if t["id"] in keep]
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%m%d%H%M")
    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        results = list(ex.map(lambda t: run_task(t, a.mode, stamp), tasks))
    out = RESULTS / f"{a.mode}.json"
    previous = {r["task"]: r for r in json.loads(out.read_text())} if out.exists() else {}
    previous.update({r["task"]: r for r in results})
    out.write_text(json.dumps(list(previous.values()), indent=2))
    (RESULTS / "summary.md").write_text(summary_md())
    print((RESULTS / "summary.md").read_text())


if __name__ == "__main__":
    main()
