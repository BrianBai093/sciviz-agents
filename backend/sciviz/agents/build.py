"""Assemble the multi-agent system on Deep Agents (DECISIONS D5, D6).

Lead (main agent, no code execution) delegates via the `task` tool to three declarative sub-agents with
isolated contexts: data, analyst, viz. The Critic is not a sub-agent: it is called by the verification gate
inside `submit_viz`, so the Lead cannot skip it.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from deepagents import GeneralPurposeSubagentProfile, HarnessProfile, create_deep_agent, register_harness_profile
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from langchain.agents.middleware import (ModelCallLimitMiddleware, ModelRetryMiddleware, TodoListMiddleware,
                                       ToolErrorMiddleware)
from langgraph.checkpoint.sqlite import SqliteSaver

from ..config import settings
from ..session import Session
from ..tools.data_tools import artifact_tools, catalog_tools, python_tool, sql_tool
from ..tools.discovery_tools import discovery_tools
from ..tools.external_tools import openalex_tools
from ..tools.lead_tools import lead_tools
from ..tools.reproduce_tools import claim_plan_tools, input_tools
from ..tools.viz_tools import viz_tools
from .models import EscalationMiddleware, make_llm

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
_profiles_registered = False


def _register_profiles() -> None:
    """No shell `execute` tool and no generic catch-all sub-agent: work goes to our specialists."""
    global _profiles_registered
    if _profiles_registered:
        return
    for model in {settings.model, settings.escalation_model}:
        register_harness_profile(model, HarnessProfile(
            excluded_tools=frozenset({"execute"}),
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ))
    _profiles_registered = True


def prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text()


def lead_prompt(s: Session) -> str:
    views = s.ws.views()["views"]
    lines = []
    for v in views:
        man = s.ws.load_manifest(v["viz"])
        declared = list(((man.get("params") or {}).get("properties") or {}).keys())
        lines.append(f"- {v['view_id']}: {v['viz']} '{v['title']}' | entity types: {man.get('entity_types') or '?'} | "
                     f"declared params: {declared} | current params: {json.dumps(v['params'])} | "
                     f"earlier versions: {v.get('history') or []}")
    view_text = "\n".join(lines) or "(none)"
    return prompt("lead").format(artifacts=s.ws.index_text(), decisions=s.ws.decisions_text(), views=view_text,
                                 dataset=s.dataset.overview())


def _strip_report(text: str) -> str:
    """Sub-agent prompts end with a 'Report' section for the Lead; a single agent answers the user directly."""
    i = text.find("## Report")
    return text[:i].rstrip() if i >= 0 else text


def single_prompt(s: Session) -> str:
    """Single-agent mode (ablation, DECISIONS D40): the same role knowledge, merged into one prompt."""
    lead = lead_prompt(s)
    how = lead[lead.find("## How to work"):]
    how = how.replace("Delegate with complete briefs", "Work through the steps yourself")
    return "\n\n".join([
        prompt("single"),
        "# Working with the data\n" + _strip_report(prompt("data")).split("\n", 1)[1],
        "# Analysis\n" + _strip_report(prompt("analyst")).split("\n", 1)[1],
        "# Visualization\n" + _strip_report(prompt("viz")).split("\n", 1)[1],
        "# Overall process and answer\n" + how,
    ])


def build_single_agent(s: Session, checkpointer=None):
    _register_profiles()
    backend = FilesystemBackend(root_dir=s.ws.root, virtual_mode=True)
    tools = [*catalog_tools(s, "single"), sql_tool(s, "single"), python_tool(s, "single"),
             *artifact_tools(s, "single"), *discovery_tools(s, "single"), *viz_tools(s, "single"), *lead_tools(s)]
    return create_deep_agent(
        model=make_llm("single"), tools=tools, system_prompt=single_prompt(s), subagents=[],
        middleware=[TodoListMiddleware(), *_limits(160), EscalationMiddleware(s, "single")],
        backend=backend, checkpointer=checkpointer if checkpointer is not None else checkpointer_for(s), name="single",
    )


def checkpointer_for(s: Session) -> SqliteSaver:
    return SqliteSaver(sqlite3.connect(str(s.ws.root / "checkpoints.sqlite"), check_same_thread=False))


def _tool_error(exc: Exception) -> str:
    """A failing tool must not abort the agent run: report the failure to the model (DECISIONS D43)."""
    return f"Tool failed with {type(exc).__name__}: {str(exc)[:500]}. Adjust the call or try another approach."


def _limits(n: int) -> list:
    return [ModelCallLimitMiddleware(run_limit=n), ModelRetryMiddleware(max_retries=2),
            ToolErrorMiddleware(on_error=_tool_error)]


def build_multi_agent(s: Session, checkpointer=None):
    _register_profiles()
    backend = FilesystemBackend(root_dir=s.ws.root, virtual_mode=True)
    data_agent = {
        "name": "data",
        "description": "Data specialist: maps questions to tables/fields, filters, cleans and saves analysis-ready "
                       "tables as artifacts. Knows the dataset's scope, caveats and counting rules.",
        "system_prompt": prompt("data"),
        "tools": [*catalog_tools(s, "data"), sql_tool(s, "data"), python_tool(s, "data"), *artifact_tools(s, "data")],
        "model": make_llm("data"),
        "middleware": _limits(40),
    }
    analyst_agent = {
        "name": "analyst",
        "description": "Analysis specialist: statistics, derived measures, networks, hierarchies, clustering, layouts "
                       "and other computations in Python; saves results as artifacts and records findings.",
        "system_prompt": prompt("analyst"),
        "tools": [*catalog_tools(s, "analyst"), sql_tool(s, "analyst"), python_tool(s, "analyst"),
                  *artifact_tools(s, "analyst")],
        "model": make_llm("analyst"),
        "middleware": _limits(40),
    }
    viz_agent = {
        "name": "viz",
        "description": "Visualization engineer: designs and implements an interactive view from artifacts as a JS "
                       "module, checks it headlessly and submits it to the review gate. Returns an approved viz id.",
        "system_prompt": prompt("viz"),
        "tools": [*artifact_tools(s, "viz"), python_tool(s, "viz"), *discovery_tools(s, "viz"), *viz_tools(s, "viz")],
        "model": make_llm("viz"),
        "middleware": [*_limits(60), EscalationMiddleware(s, "viz")],
    }
    return create_deep_agent(
        model=make_llm("lead"),
        tools=[*artifact_tools(s, "lead"), *lead_tools(s)],
        system_prompt=lead_prompt(s),
        subagents=[data_agent, analyst_agent, viz_agent],
        middleware=[TodoListMiddleware(), FilesystemMiddleware(backend=backend, tools=["ls", "read_file"]),
                    *_limits(40)],
        backend=backend,
        checkpointer=checkpointer if checkpointer is not None else checkpointer_for(s),
        name="lead",
    )


KERNEL_API_DOC = (
    "\nExternal API helpers (report mode): `openalex(path, params)` -> parsed JSON; "
    "`openalex_many([(path, params), ...], workers=8)` -> results in order (Exception objects for failures); "
    "`openalex_usage()` -> requests, cache hits and cost so far. The harness handles the key, caching, rate "
    "limits and the budget."
)


def reproduce_lead_prompt(s: Session) -> str:
    return prompt("reproduce_lead").format(artifacts=s.ws.index_text(), decisions=s.ws.decisions_text(),
                                           dataset=s.dataset.overview())


def build_reproduce_agent(s: Session, checkpointer=None):
    """Report mode (Project 2, PLAN_P2 §3): a Lead with a claim plan, plus data and analyst specialists that
    can use the external API. Figure and writing roles are added in later milestones."""
    _register_profiles()
    backend = FilesystemBackend(root_dir=s.ws.root, virtual_mode=True)

    def kernel_tool(agent: str):
        t = python_tool(s, agent)
        t.description += KERNEL_API_DOC
        return t

    data_agent = {
        "name": "data",
        "description": "Data specialist: local dataset and external scholarly API. Designs, costs, pilots, runs and "
                       "validates data collection; saves analysis-ready tables with definitions and coverage.",
        "system_prompt": prompt("reproduce_data"),
        "tools": [*catalog_tools(s, "data"), sql_tool(s, "data"), kernel_tool("data"), *artifact_tools(s, "data"),
                  *openalex_tools(s, "data"), *input_tools(s, "data")],
        "model": make_llm("data"),
        "middleware": _limits(60),
    }
    analyst_agent = {
        "name": "analyst",
        "description": "Analysis specialist: computes the study's measures, statistics, models and robustness checks "
                       "in Python; saves results and records findings with numbers and sample sizes.",
        "system_prompt": prompt("reproduce_analyst"),
        "tools": [*catalog_tools(s, "analyst"), sql_tool(s, "analyst"), kernel_tool("analyst"),
                  *artifact_tools(s, "analyst"), *input_tools(s, "analyst")],
        "model": make_llm("analyst"),
        "middleware": _limits(60),
    }
    return create_deep_agent(
        model=make_llm("lead"),
        tools=[*artifact_tools(s, "lead"), *claim_plan_tools(s), *input_tools(s, "lead")],
        system_prompt=reproduce_lead_prompt(s),
        subagents=[data_agent, analyst_agent],
        middleware=[TodoListMiddleware(), FilesystemMiddleware(backend=backend, tools=["ls", "read_file"]),
                    *_limits(40)],
        backend=backend,
        checkpointer=checkpointer if checkpointer is not None else checkpointer_for(s),
        name="lead",
    )
