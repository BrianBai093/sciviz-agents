"""Data tools: catalog lookup, read-only SQL, Python execution, artifacts, decision log.

Each factory returns LangChain tools bound to one session and one agent name, so every call is
attributed to its caller in the event log.
"""
from __future__ import annotations

import json
import threading

from langchain_core.tools import tool

from ..harness.workspace import summarize_table
from ..session import Session
from .python_exec import truncate


def _emit_call(s: Session, agent: str, name: str, args: dict) -> None:
    s.events.emit(agent, "tool_call", tool=name, args={k: (truncate(str(v), 1500)) for k, v in args.items()})


def _emit_result(s: Session, agent: str, name: str, ok: bool, text: str) -> None:
    s.events.emit(agent, "tool_result", tool=name, ok=ok, result=truncate(text, 2500))


def catalog_tools(s: Session, agent: str):
    @tool
    def list_tables() -> str:
        """Overview of the dataset: what it contains, every table with its row count and meaning,
        scope exclusions, caveats, counting rules and join relationships. Call this first."""
        _emit_call(s, agent, "list_tables", {})
        text = s.dataset.full_notes()
        _emit_result(s, agent, "list_tables", True, text)
        return text

    @tool
    def describe_table(table: str) -> str:
        """Columns of one table with types, null rates, distinct counts, value ranges, top values,
        examples and meaning."""
        _emit_call(s, agent, "describe_table", {"table": table})
        text = s.dataset.describe_table(table)
        _emit_result(s, agent, "describe_table", True, text)
        return text

    @tool
    def search_catalog(query: str) -> str:
        """Find tables/columns whose name, description or common values mention the query text."""
        _emit_call(s, agent, "search_catalog", {"query": query})
        text = s.dataset.search(query)
        _emit_result(s, agent, "search_catalog", True, text)
        return text

    return [list_tables, describe_table, search_catalog]


def sql_tool(s: Session, agent: str, timeout_s: int = 60):
    @tool
    def run_sql(query: str, max_rows: int = 20, save_as_title: str = "", description: str = "") -> str:
        """Run a read-only SQL query (DuckDB dialect) against the dataset.
        Returns the row count and the first `max_rows` rows. If `save_as_title` is given, the full
        result is saved as a table artifact and its id is returned (use this for results other
        agents or visualizations need)."""
        _emit_call(s, agent, "run_sql", {"query": query, "save_as_title": save_as_title})
        con = s.dataset.connect()
        timer = threading.Timer(timeout_s, con.interrupt)
        timer.start()
        try:
            df = con.execute(query).df()
        except Exception as e:  # report to the model so it can fix the query
            text = f"SQL error: {type(e).__name__}: {e}"
            _emit_result(s, agent, "run_sql", False, text)
            return text
        finally:
            timer.cancel()
            con.close()
        text = f"{len(df):,} rows x {df.shape[1]} columns.\n" + df.head(max_rows).to_string(max_colwidth=60, index=False)
        if save_as_title:
            meta = s.ws.save_table(df, save_as_title, description, producer=agent, code=query)
            s.events.emit(agent, "artifact", id=meta["id"], artifact_kind="table", title=save_as_title)
            text = f"Saved as artifact {meta['id']}.\n" + text
        _emit_result(s, agent, "run_sql", True, text)
        return truncate(text, 6000)

    return run_sql


def python_tool(s: Session, agent: str):
    @tool
    def run_python(code: str) -> str:
        """Execute Python in your persistent kernel (state survives between calls).
        Preloaded: pandas as pd, numpy as np, `db` (read-only DuckDB connection), `sql(query)` -> DataFrame,
        `load(artifact_id)`, `save_table(df, title, description)`, `save_graph(nodes, edges, title, description)`,
        `save_json(obj, kind, title, description)` with kind in graph|tree|json|finding,
        `record_finding(text, value)`. Available libraries include scipy, networkx, scikit-learn and statsmodels.
        Print what you need to see; outputs are truncated."""
        _emit_call(s, agent, "run_python", {"code": code})
        before = {m["id"] for m in s.ws.list()}
        ok, text = s.kernels.run(agent, code)
        for m in s.ws.list():
            if m["id"] not in before and m["kind"] != "viz":
                prev = m.get("code") or ""
                s.ws.update_meta(m["id"], code=(prev + "\n\n" if prev else "") + code)
                s.events.emit(agent, "artifact", id=m["id"], artifact_kind=m["kind"], title=m["title"])
        _emit_result(s, agent, "run_python", ok, text)
        return text

    return run_python


def artifact_tools(s: Session, agent: str):
    @tool
    def list_artifacts() -> str:
        """All artifacts in this session: id, kind, title, one-line summary and lineage (inputs)."""
        return s.ws.index_text()

    @tool
    def inspect_artifact(artifact_id: str) -> str:
        """Summary of one artifact: schema, size, statistics, preview rows, producer and lineage."""
        _emit_call(s, agent, "inspect_artifact", {"artifact_id": artifact_id})
        try:
            text = s.ws.describe(artifact_id)
        except KeyError as e:
            text = str(e)
        _emit_result(s, agent, "inspect_artifact", True, text)
        return text

    @tool
    def record_decision(text: str) -> str:
        """Record a definition or assumption you made (e.g. how a term in the question was operationalized)
        so later steps and the final answer stay consistent."""
        s.ws.add_decision(agent, text)
        s.events.emit(agent, "plan", decision=text)
        return "recorded"

    return [list_artifacts, inspect_artifact, record_decision]


def table_summary_text(df) -> str:
    return summarize_table(df)["text"]


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, default=str)
