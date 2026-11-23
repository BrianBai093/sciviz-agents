"""Tools only the Lead has: manage what the user sees and ask the user questions."""
from __future__ import annotations

import time

from langchain_core.tools import tool
from langgraph.types import interrupt

from ..session import Session


def lead_tools(s: Session):
    def _views():
        return s.ws.views()

    def _find(views: dict, ref: str) -> dict | None:
        return next((v for v in views["views"] if ref in (v["view_id"], v["viz"])), None)

    @tool
    def show_view(viz_artifact_id: str, title: str = "") -> str:
        """Show an approved visualization artifact to the user as a view. Returns the view id."""
        try:
            meta = s.ws.get(viz_artifact_id)
        except KeyError as e:
            return str(e)
        if meta["kind"] != "viz" or meta.get("status") not in ("approved", "approved_with_issues"):
            return f"{viz_artifact_id} is not an approved visualization (status: {meta.get('status')}); it cannot be shown."
        views = _views()
        existing = next((v for v in views["views"] if v["viz"] == viz_artifact_id), None)
        if existing:
            return f"{viz_artifact_id} is already shown as {existing['view_id']}."
        view_id = f"view{len(views['views']) + 1}"
        views["views"].append({"view_id": view_id, "viz": viz_artifact_id, "title": title or meta["title"],
                               "params": {}, "highlight": [], "created_at": time.time()})
        s.ws.save_views(views)
        s.events.emit("lead", "view", action="show", view_id=view_id, viz=viz_artifact_id, title=title or meta["title"])
        return f"Showing {viz_artifact_id} as {view_id}."

    @tool
    def set_view_params(view: str, params: dict) -> str:
        """Change parameter values of a shown view (by view id or viz artifact id) without new code.
        Only parameters declared in the visualization's manifest can be set."""
        views = _views()
        v = _find(views, view)
        if not v:
            return f"No view {view!r}. Shown views: {[x['view_id'] for x in views['views']]}"
        manifest = s.ws.load_manifest(v["viz"]) if hasattr(s.ws, "load_manifest") else {}
        declared = set(((manifest.get("params") or {}).get("properties") or {}).keys())
        unknown = [k for k in params if declared and k not in declared]
        if unknown:
            return f"Unknown parameters {unknown}; this view declares {sorted(declared)}."
        v["params"].update(params)
        s.ws.save_views(views)
        s.events.emit("lead", "view", action="params", view_id=v["view_id"], params=params)
        return f"Updated {v['view_id']} parameters: {params}"

    @tool
    def highlight_view(view: str, items: list[dict]) -> str:
        """Highlight items in a shown view. Items look like {"type": "<entity type>", "id": "<dataset id>"} or
        {"type": "group", "key": {...}}; pass [] to clear."""
        views = _views()
        v = _find(views, view)
        if not v:
            return f"No view {view!r}."
        v["highlight"] = items
        s.ws.save_views(views)
        s.events.emit("lead", "view", action="highlight", view_id=v["view_id"], items=items)
        return f"Highlighted {len(items)} item(s) in {v['view_id']}."

    @tool
    def ask_user(question: str) -> str:
        """Ask the user a clarifying question and wait for the answer. Use sparingly: only when different
        readings of the request would lead to fundamentally different answers."""
        s.events.emit("lead", "interrupt", question=question)
        return str(interrupt({"question": question}))

    return [show_view, set_view_params, highlight_view, ask_user]
