"""One user turn, shared by the CLI and the web API.

Builds the agent graph for the session (fresh each turn, so the Lead's prompt carries the current artifacts,
decisions and views), sends the user message plus any selection made in the views, handles interrupts
(clarifying questions) through a callback, and emits message/done/error events.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable

from langgraph.types import Command

from .agents.build import build_multi_agent, build_single_agent
from .agents.models import TraceCallback
from .session import Session

AnswerFn = Callable[[str], str]


def format_selection(s: Session, selection: dict | None) -> str:
    """Turn a UI selection into text the Lead can act on (dataset ids, labels, the view it came from)."""
    if not selection or not selection.get("items"):
        return ""
    view = selection.get("view_id") or ""
    viz = selection.get("viz") or ""
    entity_types = []
    if viz:
        try:
            entity_types = s.ws.load_manifest(viz).get("entity_types") or []
        except Exception:
            entity_types = []
    items = []
    for it in selection["items"][:50]:
        ident = f"id={it['id']}" if it.get("id") is not None else f"key={json.dumps(it.get('key'))}"
        items.append(f"{it.get('type', 'item')} {ident}" + (f" ({it['label']})" if it.get("label") else ""))
    more = f" and {len(selection['items']) - 50} more" if len(selection["items"]) > 50 else ""
    return (f"\n\n[The user currently has {len(selection['items'])} item(s) selected in {view} ({viz}"
            f"{', entity types: ' + ', '.join(entity_types) if entity_types else ''}): "
            + "; ".join(items) + more + "]")


def run_turn(s: Session, text: str, selection: dict | None = None, answer_fn: AnswerFn | None = None,
             mode: str = "multi") -> str:
    t0 = time.time()
    cost0 = s.ledger.session_total(s.id)
    s.user_question = text
    s.events.emit("user", "message", text=text, selection=selection)
    try:
        agent = build_single_agent(s) if mode == "single" else build_multi_agent(s)
        cfg = {"configurable": {"thread_id": s.id}, "callbacks": [s.usage_callback, TraceCallback(s)],
               "recursion_limit": 300}
        inp = {"messages": [{"role": "user", "content": text + format_selection(s, selection)}]}
        while True:
            interrupted = None
            for chunk in agent.stream(inp, cfg, stream_mode="updates"):
                if isinstance(chunk, dict) and "__interrupt__" in chunk:
                    interrupted = chunk["__interrupt__"]
            if not interrupted:
                break
            question = interrupted[0].value.get("question", "?")
            answer = answer_fn(question) if answer_fn else "Use your best judgement and state your assumption."
            s.events.emit("user", "message", text=answer, answer_to=question)
            inp = Command(resume=answer)
        final = agent.get_state(cfg).values["messages"][-1].text
        s.events.emit("lead", "message", text=final)
        return final
    except Exception as e:
        s.events.emit("system", "error", message=f"{type(e).__name__}: {e}")
        raise
    finally:
        s.events.emit("system", "done", seconds=round(time.time() - t0, 1),
                      cost=round(s.ledger.session_total(s.id) - cost0, 4), ledger_total=round(s.ledger.total, 4))
