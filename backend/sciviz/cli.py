"""Command-line interface (milestone M1): ask a question, watch the agents work, get views + answer.

  uv run sciviz ask "How has publication output per field changed from 2021 to 2024?"
  uv run sciviz ask "Now only show the top 5 fields" --session <id>      # follow-up in the same session
  uv run sciviz cost
"""
from __future__ import annotations

import json
import time

import typer
from langgraph.types import Command
from rich.console import Console
from rich.markdown import Markdown

from .agents.build import build_multi_agent
from .agents.models import TraceCallback
from .harness.budget import SpendLedger
from .session import Session

app = typer.Typer(add_completion=False, help="sciviz: multi-agent analysis of scholarly data with interactive views")
console = Console()
COLORS = {"lead": "magenta", "data": "cyan", "analyst": "green", "viz": "yellow", "critic": "red", "gate": "red"}


def _first_line(text: str, n: int = 140) -> str:
    line = next((x for x in str(text).splitlines() if x.strip()), "")
    return line[:n] + ("…" if len(line) > n else "")


def _printer(ev: dict) -> None:
    a, k, p = ev["agent"], ev["kind"], ev["payload"]
    c = COLORS.get(a, "white")
    if k == "delegate":
        goal = next((x for x in str(p.get("brief", "")).splitlines() if x.upper().startswith("GOAL")), "")
        console.print(f"[bold {COLORS.get(p.get('to'), 'white')}]lead → {p.get('to')}[/] {goal[:160]}")
    elif k == "report":
        console.print(f"[bold]report[/] {_first_line(p.get('text', ''))}")
    elif k == "tool_call" and p.get("tool") not in ("list_artifacts",):
        args = p.get("args", {})
        brief = args.get("slug") or args.get("table") or args.get("query") or args.get("code") or ""
        console.print(f"  [{c}]{a}[/] {p['tool']} [dim]{_first_line(brief, 100)}[/]")
    elif k == "tool_result" and not p.get("ok"):
        console.print(f"    [red]✗ {p['tool']}[/] [dim]{_first_line(p.get('result', ''), 140)}[/]")
    elif k == "artifact":
        console.print(f"  [{c}]{a}[/] saved [bold]{p['id']}[/] ({p.get('artifact_kind')}) {p.get('title')}")
    elif k == "gate":
        verdict = p.get("verdict")
        style = "green" if verdict == "pass" else "red"
        console.print(f"  [bold {style}]gate {p.get('artifact')}: {verdict}[/] {p.get('stage', '')} "
                      f"{p.get('scores', '')} [dim]{_first_line(p.get('summary', '') or '; '.join(p.get('problems', [])), 160)}[/]")
    elif k == "view":
        console.print(f"  [bold magenta]view[/] {p.get('action')} {p.get('view_id')} {p.get('viz', '')} {p.get('title', '')}")
    elif k == "plan" and p.get("escalation"):
        console.print(f"  [bold red]escalation[/] {p['escalation']}")
    elif k == "plan" and p.get("decision"):
        console.print(f"  [{c}]{a} decided[/] {_first_line(p['decision'], 160)}")


@app.command()
def ask(question: str, session: str = typer.Option(None, help="continue an existing session id"),
        selection: str = typer.Option(None, help="JSON list of selected items to attach (simulates UI selection)"),
        quiet: bool = typer.Option(False, help="do not print agent events")):
    """Ask a question (optionally continuing a session)."""
    s = Session(session)
    s.user_question = question
    if not quiet:
        s.events.subscribe(_printer)
    agent = build_multi_agent(s)
    cfg = {"configurable": {"thread_id": s.id}, "callbacks": [s.usage_callback, TraceCallback(s)],
           "recursion_limit": 300}
    content = question if not selection else f"{question}\n\n[Current selection in the views: {selection}]"
    s.events.emit("user", "message", text=content)
    console.print(f"[dim]session {s.id}[/]")
    t0 = time.time()
    inp = {"messages": [{"role": "user", "content": content}]}
    try:
        while True:
            interrupted = None
            for chunk in agent.stream(inp, cfg, stream_mode="updates"):
                if isinstance(chunk, dict) and "__interrupt__" in chunk:
                    interrupted = chunk["__interrupt__"]
            if not interrupted:
                break
            q = interrupted[0].value.get("question", "?")
            answer = typer.prompt(f"? {q}")
            s.events.emit("user", "message", text=answer)
            inp = Command(resume=answer)
        final = agent.get_state(cfg).values["messages"][-1].text
        s.events.emit("lead", "message", text=final)
        console.rule("answer")
        console.print(Markdown(final))
        console.rule()
        for v in s.ws.views()["views"]:
            shots = sorted((s.ws.artifact_dir(v["viz"]) / "shots").glob("default.png"))
            console.print(f"{v['view_id']}: {v['viz']} {v['title']} -> {shots[0] if shots else ''}")
    finally:
        spent = s.ledger.session_total(s.id)
        console.print(f"[dim]{time.time() - t0:.0f}s, session cost ${spent:.3f}, ledger total ${s.ledger.total:.2f}[/]")
        s.close()


@app.command()
def cost():
    """Show the spend ledger."""
    console.print_json(json.dumps(SpendLedger()._load()))


if __name__ == "__main__":
    app()
