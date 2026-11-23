"""Python execution environment: one Jupyter kernel per (session, agent).

Kernels run in a separate process, inside the session workspace, with every secret removed from
their environment (DECISIONS D10). A prelude gives agent code read-only SQL access to the dataset
and helpers to load/save artifacts; artifacts created during a call are tagged with that call's code.
"""
from __future__ import annotations

import os
import queue
import subprocess
import re
import threading

from jupyter_client.manager import KernelManager

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SECRET_PATTERN = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.I)
SECRET_PREFIXES = ("OPENAI", "ANTHROPIC", "OPENALEX", "DEEPSEEK", "LANGSMITH", "LANGCHAIN", "AWS", "GOOGLE", "AZURE")

PRELUDE = r'''
import os as _os, json as _json, warnings as _warnings
_warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, duckdb as _duckdb
from sciviz.harness.workspace import Workspace as _Workspace
_ws = _Workspace.open(_os.environ["SCIVIZ_WORKSPACE"])
_AGENT = _os.environ.get("SCIVIZ_AGENT", "?")
db = _duckdb.connect(_os.environ["SCIVIZ_DB"], read_only=True)
_loaded = []
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 30)

def sql(query):
    """Run read-only SQL against the dataset; returns a pandas DataFrame."""
    return db.execute(query).df()

def load(artifact_id):
    """Load an artifact: tables -> DataFrame; graph/tree/json/finding -> Python object."""
    _loaded.append(artifact_id)
    return _ws.load_data(artifact_id)

def _records(x):
    return _json.loads(x.to_json(orient="records", date_format="iso")) if hasattr(x, "to_json") else list(x)

def save_table(df, title, description=""):
    """Save a DataFrame as a table artifact; returns its id."""
    m = _ws.save_table(df, title, description, producer=_AGENT, inputs=sorted(set(_loaded)))
    print(f"[saved {m['id']}: {title}]"); return m["id"]

def save_json(obj, kind, title, description=""):
    """Save a JSON-serializable object as an artifact of kind 'graph', 'tree', 'json' or 'finding'."""
    m = _ws.save_json(obj, kind, title, description, producer=_AGENT, inputs=sorted(set(_loaded)))
    print(f"[saved {m['id']}: {title}]"); return m["id"]

def save_graph(nodes, edges, title, description=""):
    """Save a graph: nodes need an 'id' field, edges need 'source' and 'target' fields."""
    return save_json({"nodes": _records(nodes), "edges": _records(edges)}, "graph", title, description)

def record_finding(text, value=None, title=None):
    """Record a factual finding (a claim with its numbers) so the final answer can cite it."""
    return save_json({"text": text, "value": value}, "finding", title or text[:60])
'''


def clean_env(extra: dict[str, str]) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items()
           if not SECRET_PATTERN.search(k) and not k.upper().startswith(SECRET_PREFIXES)}
    env.update(extra)
    env["MPLBACKEND"] = "Agg"
    return env


def truncate(text: str, limit: int = 8000) -> str:
    if len(text) <= limit:
        return text
    head, tail = text[: limit // 3], text[-(2 * limit) // 3:]
    return f"{head}\n... [{len(text) - limit:,} characters truncated] ...\n{tail}"


class KernelPool:
    def __init__(self, workspace_root, db_path):
        self.workspace_root = str(workspace_root)
        self.db_path = str(db_path)
        self._kernels: dict[str, tuple[KernelManager, object]] = {}
        self._lock = threading.Lock()

    def _start(self, agent: str):
        km = KernelManager(kernel_name="python3")
        km.start_kernel(cwd=self.workspace_root, env=clean_env({
            "SCIVIZ_WORKSPACE": self.workspace_root, "SCIVIZ_DB": self.db_path, "SCIVIZ_AGENT": agent,
        }), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # kernel chatter (e.g. transport warnings) is noise
        kc = km.client()
        kc.start_channels()
        kc.wait_for_ready(timeout=60)
        reply = kc.execute_interactive(PRELUDE, timeout=120, store_history=False, output_hook=lambda m: None)
        if reply["content"]["status"] != "ok":
            raise RuntimeError(f"kernel prelude failed: {reply['content']}")
        return km, kc

    def run(self, agent: str, code: str, timeout: int = 180) -> tuple[bool, str]:
        with self._lock:
            if agent not in self._kernels:
                self._kernels[agent] = self._start(agent)
            km, kc = self._kernels[agent]
        out: list[str] = []
        err: list[str] = []

        def hook(msg):
            t, c = msg["msg_type"], msg["content"]
            if t == "stream":
                out.append(c["text"])
            elif t in ("execute_result", "display_data"):
                data = c.get("data", {})
                if "text/plain" in data:
                    out.append(data["text/plain"] + "\n")
                elif any(k.startswith("image/") for k in data):
                    out.append("[image output omitted: images are not shown to agents]\n")
            elif t == "error":
                tb = ANSI.sub("", "\n".join(c.get("traceback", [])))
                err.append("\n".join(tb.splitlines()[-40:]))

        try:
            reply = kc.execute_interactive(code, timeout=timeout, output_hook=hook)
            ok = reply["content"]["status"] == "ok"
        except (TimeoutError, queue.Empty):
            km.interrupt_kernel()
            return False, f"Execution timed out after {timeout}s and was interrupted. Make the computation smaller."
        text = "".join(out)
        if err:
            text += ("\n" if text else "") + "ERROR:\n" + "\n".join(err)
        return ok, truncate(text.strip() or "(no output)")

    def shutdown(self) -> None:
        for km, kc in self._kernels.values():
            try:
                kc.stop_channels()
                km.shutdown_kernel(now=True)
            except Exception:
                pass
        self._kernels.clear()
