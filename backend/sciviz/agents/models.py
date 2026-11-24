"""Model construction, model escalation middleware and trace callbacks."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain.agents.middleware import AgentMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler

from ..config import settings

# Reasoning effort per role (DECISIONS D2, D27).
EFFORT = {"lead": "medium", "data": "medium", "analyst": "medium", "viz": "medium", "critic": "high", "single": "medium",
          "writer": "medium"}


def make_llm(role: str, model: str | None = None):
    """One model instance per role; `metadata` lets callbacks attribute every call to its agent."""
    return init_chat_model(model or settings.model, reasoning={"effort": EFFORT.get(role, "medium")},
                           metadata={"sciviz_agent": role}, tags=[f"agent:{role}"])


class EscalationMiddleware(AgentMiddleware):
    """Switches an agent to the escalation model while the verification gate says so (DECISIONS D3).

    The gate puts the agent name into `session.escalate_agents` after repeated failures and removes it
    when the cycle ends; every model call of that agent in between uses the stronger model.
    """

    def __init__(self, session, agent: str):
        super().__init__()
        self.session, self.agent = session, agent
        self._strong = None

    def wrap_model_call(self, request, handler):
        if self.agent in self.session.escalate_agents:
            if self._strong is None:
                self._strong = make_llm(self.agent, settings.escalation_model)
            request = request.override(model=self._strong)
            self.session.events.emit(self.agent, "plan", escalation=f"using {settings.escalation_model}")
        return handler(request)


class TraceCallback(BaseCallbackHandler):
    """Turns the Lead's planning and delegation tool calls into events."""

    def __init__(self, session):
        self.session = session
        self._tools: dict[UUID, str] = {}

    def on_tool_start(self, serialized: dict, input_str: str, *, run_id: UUID, inputs: dict | None = None,
                      **kw: Any) -> None:
        name = (serialized or {}).get("name", "")
        self._tools[run_id] = name
        inputs = inputs or {}
        if name == "task":
            self.session.events.emit("lead", "delegate", to=inputs.get("subagent_type"),
                                     brief=str(inputs.get("description", ""))[:4000])
        elif name == "write_todos":
            self.session.events.emit("lead", "plan", todos=inputs.get("todos"))

    def on_tool_end(self, output: Any, *, run_id: UUID, **kw: Any) -> None:
        name = self._tools.pop(run_id, "")
        if name == "task":
            text = getattr(output, "content", None) or str(output)
            if hasattr(output, "update") and isinstance(getattr(output, "update", None), dict):
                msgs = output.update.get("messages") or []
                if msgs:
                    text = getattr(msgs[-1], "content", str(msgs[-1]))
            self.session.events.emit("lead", "report", text=str(text)[:4000])
