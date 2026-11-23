"""Send one message to a session through the web API (as the UI does) and wait until the turn is done.

Usage: uv run python tests/ui/ask.py <session_id> "<text>" ['<selection json>']
Prints the view events and the final answer.
"""
import json
import sys
import time

import httpx

API = "http://localhost:8000"


def main(sid: str, text: str, selection: str | None) -> None:
    sel = json.loads(selection) if selection else None
    with httpx.Client(timeout=30) as c:
        n0 = len(c.get(f"{API}/api/sessions/{sid}/events", params={"replay": True, "speed": 1e9}).text.split("event: ev")) - 1
        r = c.post(f"{API}/api/sessions/{sid}/messages", json={"text": text, "selection": sel})
        r.raise_for_status()
        t0 = time.time()
        while True:
            time.sleep(5)
            st = c.get(f"{API}/api/sessions/{sid}").json()
            if not st["busy"]:
                break
            if st.get("question"):
                print("QUESTION:", st["question"])
        evs = [json.loads(line[6:]) for line in c.get(f"{API}/api/sessions/{sid}/events",
               params={"replay": True, "speed": 1e9}).text.splitlines() if line.startswith("data: {")]
    new = evs[n0:]
    for e in new:
        p = e["payload"]
        if e["kind"] in ("view", "gate", "delegate", "error"):
            brief = p.get("brief", "")
            goal = next((x for x in brief.splitlines() if x.upper().startswith("GOAL")), "")
            print(f"[{e['agent']}] {e['kind']}: " + json.dumps({k: v for k, v in p.items() if k not in ("brief", "issues", "summary")})[:300] + (f" {goal[:150]}" if goal else ""))
    final = next((e["payload"]["text"] for e in reversed(new) if e["kind"] == "message" and e["agent"] == "lead"), "")
    done = next((e["payload"] for e in reversed(new) if e["kind"] == "done"), {})
    print("---\n" + final[:1500] + f"\n--- {time.time() - t0:.0f}s, {done}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
