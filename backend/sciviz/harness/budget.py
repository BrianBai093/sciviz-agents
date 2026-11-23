"""Spend ledger (DECISIONS D18): records every LLM call's tokens and cost, warns and hard-stops.

The ledger is a JSON file shared by all sessions (workspaces/_ledger.json). A LangChain callback
handler captures usage from every chat-model call, including calls made inside sub-agents.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from ..config import PRICES, settings


class BudgetExceeded(RuntimeError):
    pass


def cost_of(model: str, usage: dict) -> float:
    key = next((k for k in PRICES if k in (model or "")), None)
    if key is None:
        return 0.0
    p_in, p_cached, p_out = PRICES[key]
    cached = (usage.get("input_token_details") or {}).get("cache_read", 0) or 0
    fresh = max(usage.get("input_tokens", 0) - cached, 0)
    return (fresh * p_in + cached * p_cached + usage.get("output_tokens", 0) * p_out) / 1e6


class SpendLedger:
    def __init__(self, path: Path | None = None):
        self.path = path or settings.workspaces_dir / "_ledger.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.write_text(json.dumps({"total_usd": 0.0, "calls": 0, "by_model": {}, "by_session": {}}))

    def _load(self) -> dict:
        return json.loads(self.path.read_text())

    @property
    def total(self) -> float:
        return self._load()["total_usd"]

    def check(self) -> None:
        if self.total >= settings.budget_usd:
            raise BudgetExceeded(
                f"LLM budget exhausted: ${self.total:.2f} spent of ${settings.budget_usd:.2f}. Ask the user before continuing."
            )

    def record(self, session: str, agent: str, model: str, usage: dict) -> float:
        usd = cost_of(model, usage)
        with self._lock:
            d = self._load()
            d["total_usd"] = round(d["total_usd"] + usd, 6)
            d["calls"] += 1
            m = d["by_model"].setdefault(model, {"usd": 0.0, "input": 0, "cached": 0, "output": 0, "calls": 0})
            m["usd"] = round(m["usd"] + usd, 6)
            m["input"] += usage.get("input_tokens", 0)
            m["cached"] += (usage.get("input_token_details") or {}).get("cache_read", 0) or 0
            m["output"] += usage.get("output_tokens", 0)
            m["calls"] += 1
            s = d["by_session"].setdefault(session, {"usd": 0.0, "calls": 0})
            s["usd"] = round(s["usd"] + usd, 6)
            s["calls"] += 1
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(d, indent=2))
            tmp.replace(self.path)
        return usd

    def session_total(self, session: str) -> float:
        return self._load()["by_session"].get(session, {}).get("usd", 0.0)


class UsageCallback(BaseCallbackHandler):
    """Captures token usage of every chat-model call and records it in the ledger + event log."""

    def __init__(self, ledger: SpendLedger, session_id: str, events=None):
        self.ledger, self.session_id, self.events = ledger, session_id, events
        self._runs: dict[UUID, tuple[str, str, float]] = {}

    def on_chat_model_start(self, serialized: dict, messages: Any, *, run_id: UUID, metadata=None, **kw) -> None:
        metadata = metadata or {}
        model = metadata.get("ls_model_name") or (serialized or {}).get("kwargs", {}).get("model") or "unknown"
        agent = metadata.get("sciviz_agent") or metadata.get("lc_agent_name") or "lead"
        self.ledger.check()
        self._runs[run_id] = (model, agent, time.time())

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kw) -> None:
        model, agent, t0 = self._runs.pop(run_id, ("unknown", "?", time.time()))
        usage: dict = {}
        for gens in response.generations:
            for g in gens:
                msg = getattr(g, "message", None)
                if msg is not None and getattr(msg, "usage_metadata", None):
                    usage = dict(msg.usage_metadata)
        if not usage:
            return
        usd = self.ledger.record(self.session_id, agent, model, usage)
        if self.events is not None:
            self.events.emit(agent, "cost", model=model, usd=round(usd, 5), seconds=round(time.time() - t0, 2),
                             input_tokens=usage.get("input_tokens", 0), output_tokens=usage.get("output_tokens", 0),
                             cached_tokens=(usage.get("input_token_details") or {}).get("cache_read", 0),
                             ledger_total=round(self.ledger.total, 4))
