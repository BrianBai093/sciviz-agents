"""Session workspace and artifact store (PLAN §3.4).

Layout of workspaces/<session_id>/:
  artifacts/<id>/meta.json        metadata: kind, title, producer, inputs (lineage), code, summary, ...
  artifacts/<id>/data.parquet     tables
  artifacts/<id>/data.json        graphs, trees, generic JSON, findings
  viz/<slug>/module.js, viz.json  visualization sources written by the Viz agent
  artifacts/<id>/shots/*.png      screenshots taken by the verification gate (viz artifacts)
  decisions.jsonl                 definitions/assumptions recorded by agents
  views.json                      what the UI shows (view -> viz artifact, params, highlight)
  events.jsonl                    event log (see events.py)

This module is imported both by the harness and inside the Python kernels (prelude).
"""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Any

import pandas as pd

KINDS = ("table", "graph", "tree", "json", "finding", "viz")
_lock = threading.Lock()


def _now() -> float:
    return round(time.time(), 3)


class Workspace:
    def __init__(self, root: Path, session_id: str | None = None):
        self.root = Path(root)
        self.session_id = session_id or self.root.name
        for d in ("artifacts", "viz"):
            (self.root / d).mkdir(parents=True, exist_ok=True)

    @classmethod
    def open(cls, root: str | Path) -> "Workspace":
        return cls(Path(root))

    # ---- ids -------------------------------------------------------------------------------
    def _next_id(self, prefix: str) -> str:
        with _lock:
            counter = self.root / ".counter.json"
            d = json.loads(counter.read_text()) if counter.exists() else {}
            d[prefix] = d.get(prefix, 0) + 1
            counter.write_text(json.dumps(d))
            return f"{prefix}{d[prefix]}"

    def artifact_dir(self, aid: str) -> Path:
        return self.root / "artifacts" / aid

    # ---- write -----------------------------------------------------------------------------
    def _write_meta(self, aid: str, meta: dict) -> dict:
        p = self.artifact_dir(aid) / "meta.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str))
        tmp.replace(p)
        return meta

    def save_table(self, df: pd.DataFrame, title: str, description: str = "", *, producer: str = "?",
                   inputs: list[str] | None = None, code: str | None = None) -> dict:
        aid = self._next_id("T")
        d = self.artifact_dir(aid)
        d.mkdir(parents=True, exist_ok=True)
        df = df.copy()
        df.columns = [str(c) for c in df.columns]
        df.to_parquet(d / "data.parquet", index=False)
        meta = {"id": aid, "kind": "table", "title": title, "description": description, "producer": producer,
                "inputs": inputs or [], "code": code, "created_at": _now(), "file": "data.parquet",
                "summary": summarize_table(df)}
        return self._write_meta(aid, meta)

    def save_json(self, obj: Any, kind: str, title: str, description: str = "", *, producer: str = "?",
                  inputs: list[str] | None = None, code: str | None = None) -> dict:
        if kind not in KINDS or kind in ("table", "viz"):
            raise ValueError(f"kind must be one of graph, tree, json, finding (got {kind!r})")
        prefix = {"graph": "G", "tree": "H", "json": "J", "finding": "F"}[kind]
        aid = self._next_id(prefix)
        d = self.artifact_dir(aid)
        d.mkdir(parents=True, exist_ok=True)
        (d / "data.json").write_text(json.dumps(obj, ensure_ascii=False, default=_json_default))
        meta = {"id": aid, "kind": kind, "title": title, "description": description, "producer": producer,
                "inputs": inputs or [], "code": code, "created_at": _now(), "file": "data.json",
                "summary": summarize_json(obj)}
        return self._write_meta(aid, meta)

    def register_viz(self, slug: str, title: str, *, producer: str, inputs: list[str], parent: str | None,
                     manifest: dict, module_code: str) -> dict:
        aid = self._next_id("V")
        d = self.artifact_dir(aid)
        (d / "shots").mkdir(parents=True, exist_ok=True)
        (d / "module.js").write_text(module_code)
        (d / "viz.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        version = 1
        if parent:
            version = self.get(parent).get("version", 1) + 1
        meta = {"id": aid, "kind": "viz", "title": title, "description": manifest.get("description", ""),
                "producer": producer, "inputs": inputs, "code": None, "created_at": _now(), "file": "module.js",
                "source_dir": f"viz/{slug}", "parent": parent, "version": version, "status": "draft",
                "reviews": [], "summary": f"visualization module ({len(module_code)} chars) bound to {inputs}"}
        return self._write_meta(aid, meta)

    def update_meta(self, aid: str, **changes) -> dict:
        meta = self.get(aid)
        meta.update(changes)
        return self._write_meta(aid, meta)

    # ---- read ------------------------------------------------------------------------------
    def get(self, aid: str) -> dict:
        p = self.artifact_dir(aid) / "meta.json"
        if not p.exists():
            raise KeyError(f"No artifact {aid!r} in this session")
        return json.loads(p.read_text())

    def load_data(self, aid: str) -> Any:
        meta = self.get(aid)
        f = self.artifact_dir(aid) / meta["file"]
        if meta["kind"] == "table":
            return pd.read_parquet(f)
        if meta["kind"] == "viz":
            return f.read_text()
        return json.loads(f.read_text())

    def data_for_browser(self, aid: str) -> Any:
        """JSON-serializable form used by the visualization runtime."""
        meta = self.get(aid)
        if meta["kind"] == "table":
            df = self.load_data(aid)
            return json.loads(df.to_json(orient="records", date_format="iso"))
        return self.load_data(aid)

    def list(self) -> list[dict]:
        metas = []
        for p in sorted((self.root / "artifacts").glob("*/meta.json"), key=lambda p: p.stat().st_mtime):
            metas.append(json.loads(p.read_text()))
        return metas

    def index_text(self) -> str:
        rows = []
        for m in self.list():
            status = f" [{m['status']}]" if m["kind"] == "viz" else ""
            lineage = f" <- {', '.join(m['inputs'])}" if m.get("inputs") else ""
            short = m["summary"] if isinstance(m["summary"], str) else m["summary"].get("one_line", "")
            rows.append(f"{m['id']} ({m['kind']}{status}) {m['title']}: {short}{lineage}")
        return "\n".join(rows) if rows else "(no artifacts yet)"

    def describe(self, aid: str) -> str:
        m = self.get(aid)
        s = m["summary"]
        body = s if isinstance(s, str) else s.get("text", json.dumps(s)[:3000])
        head = f"{m['id']} ({m['kind']}) {m['title']}\nproducer: {m['producer']}; inputs: {m.get('inputs') or '-'}"
        if m.get("description"):
            head += f"\ndescription: {m['description']}"
        if m["kind"] == "viz":
            head += f"\nstatus: {m['status']}; version: {m.get('version')}; parent: {m.get('parent')}"
        return f"{head}\n{body}"

    # ---- decisions and views ---------------------------------------------------------------
    def add_decision(self, agent: str, text: str) -> None:
        with (self.root / "decisions.jsonl").open("a", encoding="utf8") as f:
            f.write(json.dumps({"ts": _now(), "agent": agent, "text": text}, ensure_ascii=False) + "\n")

    def decisions_text(self) -> str:
        p = self.root / "decisions.jsonl"
        if not p.exists():
            return "(none yet)"
        items = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
        return "\n".join(f"- [{d['agent']}] {d['text']}" for d in items)

    def views(self) -> dict:
        p = self.root / "views.json"
        return json.loads(p.read_text()) if p.exists() else {"views": [], "selection": None}

    def save_views(self, views: dict) -> None:
        (self.root / "views.json").write_text(json.dumps(views, indent=2, ensure_ascii=False))


# ---- summaries ----------------------------------------------------------------------------
def _json_default(o):
    if hasattr(o, "item"):
        return o.item()
    if hasattr(o, "tolist"):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def summarize_table(df: pd.DataFrame, head: int = 5) -> dict:
    cols = []
    for c in df.columns:
        s = df[c]
        info = f"{c}: {s.dtype}"
        if pd.api.types.is_numeric_dtype(s) and len(s):
            info += f" [min {s.min():.4g}, max {s.max():.4g}, mean {s.mean():.4g}]"
        elif len(s):
            info += f" [{s.nunique(dropna=True)} distinct]"
        if s.isna().any():
            info += f" ({s.isna().mean() * 100:.0f}% null)"
        cols.append(info)
    preview = df.head(head).to_string(max_colwidth=40, index=False)
    text = f"{len(df):,} rows x {df.shape[1]} columns\n" + "\n".join(cols) + f"\nfirst rows:\n{preview}"
    return {"one_line": f"{len(df):,} rows; columns: {', '.join(map(str, df.columns[:12]))}", "text": text,
            "rows": len(df), "columns": list(map(str, df.columns))}


def summarize_json(obj: Any) -> dict:
    def shape(o, depth=0):
        if depth > 2:
            return "..."
        if isinstance(o, dict):
            return {k: shape(v, depth + 1) for k, v in list(o.items())[:15]}
        if isinstance(o, list):
            return f"list[{len(o)}] of " + (json.dumps(shape(o[0], depth + 1)) if o else "nothing")
        return type(o).__name__

    sk = json.dumps(shape(obj))
    text = f"structure: {sk[:1500]}\npreview: {json.dumps(obj, default=_json_default)[:1500]}"
    one = sk[:160]
    return {"one_line": one, "text": text}


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "viz"
