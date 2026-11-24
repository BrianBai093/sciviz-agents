"""A Session bundles everything one conversation needs: workspace, dataset, events, ledger, kernels.

Modes: "viz" (Project 1, the default) and "reproduce" (Project 2, PLAN_P2). Reproduce sessions live under
workspaces/reproduce/, have their own spend ledger and LLM budget, and get external API access through the
harness-side OpenAlex service; their kernels reach it via a local proxy URL (no key).
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from .config import settings
from .datasets import Dataset
from .harness.budget import SpendLedger, UsageCallback
from .harness.events import EventLog
from .harness.workspace import Workspace
from .tools.python_exec import KernelPool


@dataclass
class GateState:
    failures: int = 0
    escalated: bool = False
    last_artifact: str | None = None


class Session:
    def __init__(self, session_id: str | None = None, mode: str = "viz", external_budget_usd: float | None = None):
        self.mode = mode
        base = settings.workspaces_dir if mode == "viz" else settings.workspaces_dir / mode
        self.id = session_id or time.strftime(("s" if mode == "viz" else mode[0]) + "%Y%m%d-%H%M%S")
        self.ws = Workspace(base / self.id, self.id)
        self.dataset = Dataset(settings.db_path, settings.catalog_path)
        self.events = EventLog(self.id, self.ws.root / "events.jsonl")
        self.openalex = None
        extra_env: dict[str, str] = {}
        if mode == "viz":
            self.ledger = SpendLedger()
        else:
            from .harness.openalex import OpenAlexService
            self.ledger = SpendLedger(base / "_ledger.json", budget_usd=settings.reproduce_budget_usd)
            self.openalex = OpenAlexService(
                os.getenv("OPENALEX_API_KEY", ""), settings.openalex_cache,
                budget_usd=settings.openalex_session_budget_usd if external_budget_usd is None else external_budget_usd,
                rate_per_s=settings.openalex_rate_per_s, usage_path=self.ws.root / "external_usage.json",
                events=self.events)
            extra_env["SCIVIZ_OPENALEX_URL"] = self.openalex.start_proxy()
        self.kernels = KernelPool(self.ws.root, settings.db_path, extra_env)
        self.gates: dict[str, GateState] = {}
        self.escalate_agents: set[str] = set()
        self.user_question: str = ""
        self.usage_callback = UsageCallback(self.ledger, self.id, self.events)

    def gate(self, slug: str) -> GateState:
        return self.gates.setdefault(slug, GateState())

    def close(self) -> None:
        self.kernels.shutdown()
        if self.openalex is not None:
            self.openalex.close()


@dataclass
class ToolContext:
    """What a tool needs to know about its caller."""
    session: Session
    agent: str
    extra: dict = field(default_factory=dict)
