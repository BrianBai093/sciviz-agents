"""A Session bundles everything one conversation needs: workspace, dataset, events, ledger, kernels."""
from __future__ import annotations

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
    def __init__(self, session_id: str | None = None):
        self.id = session_id or time.strftime("s%Y%m%d-%H%M%S")
        self.ws = Workspace(settings.workspaces_dir / self.id, self.id)
        self.dataset = Dataset(settings.db_path, settings.catalog_path)
        self.events = EventLog(self.id, self.ws.root / "events.jsonl")
        self.ledger = SpendLedger()
        self.kernels = KernelPool(self.ws.root, settings.db_path)
        self.gates: dict[str, GateState] = {}
        self.escalate_agents: set[str] = set()
        self.user_question: str = ""
        self.usage_callback = UsageCallback(self.ledger, self.id, self.events)

    def gate(self, slug: str) -> GateState:
        return self.gates.setdefault(slug, GateState())

    def close(self) -> None:
        self.kernels.shutdown()


@dataclass
class ToolContext:
    """What a tool needs to know about its caller."""
    session: Session
    agent: str
    extra: dict = field(default_factory=dict)
