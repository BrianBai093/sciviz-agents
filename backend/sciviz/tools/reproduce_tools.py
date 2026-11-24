"""Tools for report mode (Project 2): read the run's input files, keep the claim plan."""
from __future__ import annotations

import json
import time

from langchain_core.tools import tool

from ..session import Session


def input_tools(s: Session, agent: str):
    @tool
    def read_input(name: str = "") -> str:
        """Read one of this run's input files (for example the paper brief). Without a name, list the files."""
        folder = s.ws.root / "inputs"
        files = sorted(p.name for p in folder.glob("*") if p.is_file()) if folder.exists() else []
        if not name:
            return "Input files: " + (", ".join(files) or "(none)")
        p = folder / name
        if name not in files:
            return f"No input file {name!r}. Input files: {', '.join(files) or '(none)'}"
        s.events.emit(agent, "tool_call", tool="read_input", args={"name": name})
        return p.read_text(encoding="utf8")

    @tool
    def read_claim_plan() -> str:
        """The run's claim plan: the study's claims with ids, evidence needed and testability."""
        p = s.ws.root / "claim_plan.json"
        return p.read_text(encoding="utf8") if p.exists() else "No claim plan has been written yet."

    return [read_input, read_claim_plan]


CLAIM_FIELDS = ("id", "claim", "source", "evidence_needed", "testable", "reason")


def claim_plan_tools(s: Session):
    @tool
    def write_claim_plan(claims: list[dict]) -> str:
        """Write (or replace) the claim plan: the study's claims this run will test. Each item needs
        `id` (e.g. "C1"), `claim` (the study's claim in one sentence), `source` (which figure, table or section
        of the study states it), `evidence_needed` (what computation on this dataset would test it),
        `testable` ("yes" | "partly" | "no") and `reason` (why, especially for "partly" and "no")."""
        problems = [f"item {i}: missing {', '.join(f for f in CLAIM_FIELDS if not c.get(f))}"
                    for i, c in enumerate(claims) if any(not c.get(f) for f in CLAIM_FIELDS)]
        problems += [f"item {i}: testable must be yes|partly|no" for i, c in enumerate(claims)
                     if str(c.get("testable", "")).lower() not in ("yes", "partly", "no")]
        if problems:
            return "Claim plan not saved: " + "; ".join(problems)
        plan = {"updated_at": time.time(), "claims": claims}
        (s.ws.root / "claim_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False))
        s.events.emit("lead", "plan", claim_plan=[f"{c['id']} [{c['testable']}] {c['claim']}" for c in claims])
        counts = {k: sum(1 for c in claims if str(c["testable"]).lower() == k) for k in ("yes", "partly", "no")}
        return f"Claim plan saved: {len(claims)} claims ({counts['yes']} testable, {counts['partly']} partly, {counts['no']} not)."

    return [write_claim_plan]
