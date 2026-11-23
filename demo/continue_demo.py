"""One-off repair used for the video session (DEVLOG M3): demo-network-2 crashed in turn 3 (D43 bug).

Rolls the session back to the end of turn 2 and re-runs turns 3-5:
- the conversation is forked from the last good LangGraph checkpoint (run_turn(..., from_checkpoint=...), D44);
- the event log is truncated after turn 2's `done` event and the view state is restored to match it.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sciviz.agents.build import build_multi_agent  # noqa: E402
from sciviz.runner import run_turn  # noqa: E402
from sciviz.session import Session  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_demo_session import STEPS, most_prolific_selection  # noqa: E402

SID = "demo-network-2"
s = Session(SID)
ev_path = s.ws.root / "events.jsonl"
lines = ev_path.read_text().splitlines()
dones = [i for i, line in enumerate(lines) if json.loads(line)["kind"] == "done"]
cut = dones[1] + 1                                   # keep turns 1-2
turn2_answer = next(json.loads(line)["payload"]["text"] for line in reversed(lines[:cut])
                    if json.loads(line)["kind"] == "message" and json.loads(line)["agent"] == "lead")
agent = build_multi_agent(s)
cfg = {"configurable": {"thread_id": SID}}
good = None
for snap in agent.get_state_history(cfg):
    msgs = snap.values.get("messages", [])
    if msgs and not snap.next and getattr(msgs[-1], "text", "") == turn2_answer:
        good = snap.config["configurable"]["checkpoint_id"]
        break
assert good, "no checkpoint at the end of turn 2"
ev_path.write_text("\n".join(lines[:cut]) + "\n")
views = s.ws.views()
for v in views["views"]:
    v["history"], v["highlight"] = [], []
views["selection"] = None
s.ws.save_views(views)
print("rolled back to checkpoint", good, "events kept:", cut)

for k, text in enumerate(STEPS[2:]):
    selection = None
    if text.startswith("@select "):
        text = text[len("@select "):]
        selection = most_prolific_selection(s)
        s.events.emit("user", "select", **selection)
    run_turn(s, text, selection, from_checkpoint=good if k == 0 else None)
    print(f"done: {text[:70]}  ${s.ledger.session_total(SID):.2f}", flush=True)
print("views:", [(v["view_id"], v["viz"], v.get("history")) for v in s.ws.views()["views"]])
s.close()
