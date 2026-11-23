"""Create the network demo session used in the video (live LLM calls, ~$1-2).

Sequence (the questions are what a user would type; nothing here is visible to the agents beyond the messages):
  1. force-directed collaboration network of the 80 most prolific researchers
  2. follow-up: the same network with hierarchical edge bundling, side by side
  3. the user selects the most prolific researcher and asks to highlight their coauthors in both views
  4. a parameter-style request
  5. a code-change request on the first view

Usage: uv run python demo/make_demo_session.py [session_id]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sciviz.runner import run_turn  # noqa: E402
from sciviz.session import Session  # noqa: E402

STEPS = [
    "Show the collaboration network among Columbia's 80 most prolific researchers in 2021-2024 as a force-directed "
    "node-link diagram.",
    "The largest group is a hairball and hard to read. Redraw the same network next to it with hierarchical edge "
    "bundling, grouping the researchers by field and subfield so that cross-field collaborations stand out. Keep the "
    "same 80 researchers so the two views can be compared.",
    "@select Highlight this researcher's coauthors in both views.",
    "In the edge-bundling view, show only the cross-field ties.",
    "In the force-directed view, color the researchers by their field and add a field legend. Keep everything else "
    "the same.",
]


def most_prolific_selection(s: Session) -> dict:
    """The user's click: the researcher with the most Columbia-affiliated works, as shown in the first view."""
    con = s.dataset.connect()
    aid, name = con.execute(
        "SELECT author_id, name FROM authors ORDER BY works_in_snapshot DESC NULLS LAST LIMIT 1").fetchone()
    con.close()
    v = s.ws.views()["views"][0]
    types = s.ws.load_manifest(v["viz"]).get("entity_types") or ["author"]
    return {"view_id": v["view_id"], "viz": v["viz"], "items": [{"type": types[0], "id": aid, "label": name}]}


def main(session_id: str | None) -> None:
    s = Session(session_id or time.strftime("demo-network-%m%d%H%M"))
    print("session", s.id, flush=True)
    for text in STEPS:
        selection = None
        if text.startswith("@select "):
            text = text[len("@select "):]
            selection = most_prolific_selection(s)
            s.events.emit("user", "select", **selection)  # what the UI logs when the user clicks
        t0 = time.time()
        run_turn(s, text, selection)
        print(f"{time.time() - t0:6.0f}s  ${s.ledger.session_total(s.id):.2f}  {text[:70]}", flush=True)
    print("views:", [(v["view_id"], v["viz"], v.get("history")) for v in s.ws.views()["views"]])
    s.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
