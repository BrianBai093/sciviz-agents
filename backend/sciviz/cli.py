"""Command-line interface (milestone M1): ask a question, watch the agents work, get views + answer.

  uv run sciviz ask "How has publication output per field changed from 2021 to 2024?"
  uv run sciviz ask "Now only show the top 5 fields" --session <id>      # follow-up in the same session
  uv run sciviz cost
"""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

from .config import settings
from .harness.budget import SpendLedger
from .runner import run_turn
from .session import Session

app = typer.Typer(add_completion=False, help="sciviz: multi-agent analysis of scholarly data with interactive views")
console = Console()
COLORS = {"lead": "magenta", "data": "cyan", "analyst": "green", "viz": "yellow", "critic": "red", "gate": "red",
          "writer": "blue"}


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
        brief = (args.get("slug") or args.get("table") or args.get("query") or args.get("code")
                 or " ".join(str(args[k]) for k in ("path", "params", "name") if args.get(k)) or "")
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
    elif k == "plan" and p.get("claim_plan"):
        console.print(f"  [{c}]{a} claim plan[/]")
        for line in p["claim_plan"]:
            console.print(f"    [dim]{_first_line(line, 160)}[/]")
    elif k == "job":
        extra = f"exit {p.get('returncode')} after {p.get('seconds')}s, created {p.get('created')}" \
            if p.get("action") == "end" else p.get("name", "")
        console.print(f"  [{c}]{a} job {p.get('action')}[/] {p.get('job')} {extra}")
    elif k == "report":
        console.print(f"  [bold blue]report {p.get('status')}[/] {p.get('pdf')}")
    elif k == "external_usage":
        console.print(f"  [dim]external API: {p.get('requests')} requests, {p.get('cache_hits')} cache hits, "
                      f"${p.get('usd', 0):.4f}[/]")
    elif k == "plan" and p.get("decision"):
        console.print(f"  [{c}]{a} decided[/] {_first_line(p['decision'], 160)}")


@app.command()
def ask(question: str, session: str = typer.Option(None, help="continue an existing session id"),
        selection: str = typer.Option(None, help="JSON list of selected items to attach (simulates UI selection)"),
        quiet: bool = typer.Option(False, help="do not print agent events")):
    """Ask a question (optionally continuing a session)."""
    s = Session(session)
    if not quiet:
        s.events.subscribe(_printer)
    console.print(f"[dim]session {s.id}[/]")
    t0 = time.time()
    sel = json.loads(selection) if selection else None
    if isinstance(sel, list):
        sel = {"items": sel}
    try:
        final = run_turn(s, question, sel, answer_fn=lambda q: typer.prompt(f"? {q}"))
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


@contextlib.contextmanager
def _one_turn_at_a_time(root: Path | None):
    """A session runs one turn at a time. A second process on the same session would interleave its event log, turn
    records and checkpoints. The lock file holds the running process's id; a lock whose process has ended is ignored."""
    if root is None:  # a new session: nothing else can be using it
        yield
        return
    lock = root / "session.lock"
    if lock.exists():
        pid = 0
        try:
            pid = int(lock.read_text().strip() or 0)
            os.kill(pid, 0)
            busy = pid > 0
        except (ValueError, ProcessLookupError):
            busy = False
        except PermissionError:
            busy = True
        if busy:
            console.print(f"[red]Session {root.name} is running in process {pid}; wait until that turn has ended.[/]")
            raise typer.Exit(1)
    root.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(os.getpid()))
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def _archive_previous_turn(root: Path) -> None:
    """A continued session keeps each earlier turn's constraints, lead report, API usage and released report (with
    its gate reviews) under history/turnN/."""
    prev = [root / "lead_report.md", root / "inputs" / "run_constraints.md", root / "external_usage.json"]
    if not any(p.exists() for p in prev):  # a stopped turn has constraints but no lead report
        return
    dest = root / "history" / f"turn{len(list((root / 'history').glob('turn*'))) + 1}"
    dest.mkdir(parents=True)
    for p in prev:
        if p.exists():
            shutil.move(p, dest / p.name)
    report = root / "report"
    if (report / "report.md").exists():  # the released report stays current until a new one passes the gate
        (dest / "report").mkdir()
        for name in ("report.md", "report.pdf", "status.json"):
            if (report / name).exists():
                shutil.copy(report / name, dest / "report" / name)
        if (report / "reviews.jsonl").exists():  # each turn's gate rounds stay with that turn
            shutil.move(report / "reviews.jsonl", dest / "report" / "reviews.jsonl")


@app.command()
def reproduce(
    paper: Path = typer.Option(..., exists=True, dir_okay=False, help="paper brief (Markdown)"),
    question: str = typer.Option(..., help="the research question"),
    constraints: Path = typer.Option(None, exists=True, dir_okay=False,
                                     help="run constraints file (e.g. a pilot); default: a full reproduction"),
    external_budget: float = typer.Option(None, help="external API budget for this session in USD"),
    extra_inputs: list[Path] = typer.Option(None, "--input", exists=True, dir_okay=False,
                                            help="additional input file for the agents (repeatable)"),
    session: str = typer.Option(None, help="session id (default: a new one)"),
    quiet: bool = typer.Option(False, help="do not print agent events"),
):
    """Report mode (Project 2): reproduce a study's findings on this dataset from a paper brief."""
    root = settings.workspaces_dir / "reproduce" / session if session else None
    with _one_turn_at_a_time(root):
        s = Session(session, mode="reproduce", external_budget_usd=external_budget)
        if not quiet:
            s.events.subscribe(_printer)
        inputs = s.ws.root / "inputs"
        inputs.mkdir(exist_ok=True)
        _archive_previous_turn(s.ws.root)
        shutil.copy(paper, inputs / "paper_brief.md")
        limits = constraints.read_text(encoding="utf8").strip() if constraints else "None: a full reproduction."
        if constraints:
            shutil.copy(constraints, inputs / "run_constraints.md")
        for f in extra_inputs or []:
            shutil.copy(f, inputs / f.name)
        message = (f"RESEARCH QUESTION: {question}\n\n"
                   f"RUN CONSTRAINTS (set by the user; they override defaults):\n{limits}\n\n"
                   f"EXTERNAL API BUDGET FOR THIS RUN: ${s.openalex.usage['budget_usd']:.2f}\n\n"
                   f"INPUT FILES (read with read_input): {', '.join(sorted(p.name for p in inputs.iterdir()))}")
        console.print(f"[dim]session {s.id} ({s.ws.root})[/]")
        t0 = time.time()
        try:
            final = run_turn(s, message, mode="reproduce")
            (s.ws.root / "lead_report.md").write_text(final, encoding="utf8")
            console.rule("lead report")
            console.print(Markdown(final))
            console.rule()
        finally:
            console.print(f"[dim]{time.time() - t0:.0f}s, LLM ${s.ledger.session_total(s.id):.3f} "
                          f"(report-mode ledger ${s.ledger.total:.2f} of ${s.ledger.budget_usd:.0f}); "
                          f"{s.openalex.usage_text()}[/]")
            s.close()


@app.command("export-run")
def export_run_cmd(session: str = typer.Option(..., help="report-mode session id"),
                   out: Path = typer.Option(..., help="output folder, e.g. reproductions/wu2019")):
    """Export a finished report-mode run: report, figures, data, frozen API responses, replayable scripts, trace."""
    from .harness.export import export_run
    ws = settings.workspaces_dir / "reproduce" / session
    if not ws.exists():
        raise typer.BadParameter(f"no report-mode session {session} under {ws.parent}")
    summary = export_run(ws, out, settings.openalex_cache)
    console.print_json(json.dumps(summary))


@app.command()
def serve(port: int = 8000, host: str = "127.0.0.1"):
    """Start the web API (and the built UI, if frontend/dist exists)."""
    import uvicorn
    uvicorn.run("sciviz.api.app:app", host=host, port=port, log_level="warning")


@app.command()
def cost():
    """Show the spend ledger."""
    console.print_json(json.dumps(SpendLedger()._load()))


if __name__ == "__main__":
    app()
