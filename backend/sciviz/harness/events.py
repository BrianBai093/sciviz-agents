"""Event log: every agent action becomes an event (shared by live UI, CLI and replay mode).

Schema: {"ts": float, "session": str, "agent": str, "kind": str, "payload": dict}
kind is one of: plan, delegate, tool_call, tool_result, artifact, gate, message, cost, error, interrupt
"""
from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from pathlib import Path

Subscriber = Callable[[dict], None]


class EventLog:
    def __init__(self, session_id: str, path: Path):
        self.session_id = session_id
        self.path = path
        self._lock = threading.Lock()
        self._subscribers: list[Subscriber] = []

    def subscribe(self, fn: Subscriber) -> None:
        self._subscribers.append(fn)

    def emit(self, agent: str, kind: str, **payload) -> dict:
        event = {"ts": time.time(), "session": self.session_id, "agent": agent, "kind": kind, "payload": payload}
        line = json.dumps(event, ensure_ascii=False, default=str)
        with self._lock:
            with self.path.open("a", encoding="utf8") as f:
                f.write(line + "\n")
        for fn in list(self._subscribers):
            try:
                fn(event)
            except Exception:  # a broken subscriber must never break the agent run
                pass
        return event

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf8").splitlines() if line.strip()]
