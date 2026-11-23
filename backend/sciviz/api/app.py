"""Web API (milestone M2): sessions, live event stream (SSE), artifacts, views, details-on-demand, replay.

Run: uv run sciviz serve   (then open the UI; in development the Vite dev server proxies /api and /runtime here)
"""
from __future__ import annotations

import asyncio
import json
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ..config import settings
from ..datasets import Dataset
from ..harness.budget import SpendLedger
from ..harness.workspace import _views_lock
from ..runner import run_turn
from ..session import Session

STATIC = Path(__file__).resolve().parent.parent / "runtime" / "static"
FRONTEND_DIST = settings.repo_root / "frontend" / "dist"

app = FastAPI(title="sciviz")
# Views run in sandboxed iframes (opaque origin), so their requests for modules and data are cross-origin.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

dataset = Dataset(settings.db_path, settings.catalog_path)


class Handle:
    def __init__(self, session: Session):
        self.session = session
        self.busy = False
        self.question: str | None = None
        self.answer: str | None = None
        self.answer_ready = threading.Event()


_hub: dict[str, Handle] = {}
_hub_lock = threading.Lock()


def _ws_dir(sid: str) -> Path:
    if "/" in sid or sid.startswith((".", "_")):
        raise HTTPException(400, "bad session id")
    return settings.workspaces_dir / sid


def handle(sid: str, create: bool = False) -> Handle:
    with _hub_lock:
        if sid not in _hub:
            if not create and not _ws_dir(sid).exists():
                raise HTTPException(404, f"no session {sid}")
            _hub[sid] = Handle(Session(sid))
        return _hub[sid]


# ---- sessions -------------------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"live": bool(os.environ.get("OPENAI_API_KEY")), "ledger_total": round(SpendLedger().total, 4),
            "budget": settings.budget_usd}


@app.get("/api/sessions")
def list_sessions():
    ledger = SpendLedger()._load().get("by_session", {})
    out = []
    for d in sorted(settings.workspaces_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not d.is_dir() or d.name.startswith((".", "_")) or not (d / "events.jsonl").exists():
            continue
        first, created = "", None
        with (d / "events.jsonl").open(encoding="utf8") as f:
            for line in f:
                e = json.loads(line)
                created = created or e["ts"]
                if e["kind"] == "message" and e["agent"] == "user":
                    first = e["payload"].get("text", "")
                    break
        views = json.loads((d / "views.json").read_text())["views"] if (d / "views.json").exists() else []
        out.append({"id": d.name, "created": created, "first_question": first[:200],
                    "cost": round(ledger.get(d.name, {}).get("usd", 0.0), 4), "views": len(views)})
    return out


@app.post("/api/sessions")
def create_session():
    s = Session()
    with _hub_lock:
        _hub[s.id] = Handle(s)
    s.events.emit("system", "session", created=True)
    return {"id": s.id}


@app.get("/api/sessions/{sid}")
def session_state(sid: str):
    h = handle(sid)
    ws = h.session.ws
    return {"id": sid, "busy": h.busy, "question": h.question, "views": ws.views()["views"],
            "artifacts": [_light(m) for m in ws.list()], "decisions": ws.decisions_text(),
            "cost": round(h.session.ledger.session_total(sid), 4)}


class MessageIn(BaseModel):
    text: str
    selection: dict | None = None


@app.post("/api/sessions/{sid}/messages", status_code=202)
def post_message(sid: str, body: MessageIn):
    h = handle(sid, create=True)
    if h.busy:
        raise HTTPException(409, "the agents are still working on the previous message")
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(503, "no OPENAI_API_KEY configured: live questions are disabled (replay still works)")

    def answer_fn(question: str) -> str:
        h.question, h.answer = question, None
        h.answer_ready.clear()
        h.answer_ready.wait(timeout=3600)
        h.question = None
        return h.answer or "Use your best judgement and state your assumption."

    def work():
        h.busy = True
        try:
            run_turn(h.session, body.text, body.selection, answer_fn)
        except Exception:
            pass  # already recorded as an error event
        finally:
            h.busy = False

    threading.Thread(target=work, daemon=True).start()
    return {"accepted": True}


class AnswerIn(BaseModel):
    answer: str


@app.post("/api/sessions/{sid}/resume")
def resume(sid: str, body: AnswerIn):
    h = handle(sid)
    if not h.question:
        raise HTTPException(409, "no question is pending")
    h.answer = body.answer
    h.answer_ready.set()
    return {"ok": True}


# ---- events: live tail or accelerated replay ----------------------------------------------------------
@app.get("/api/sessions/{sid}/events")
async def events(sid: str, request: Request, after: int = 0, replay: bool = False, speed: float = 4.0):
    path = _ws_dir(sid) / "events.jsonl"

    async def live():
        idx, pos, buf = 0, 0, ""
        while not await request.is_disconnected():
            if path.exists():
                with path.open(encoding="utf8") as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos = f.tell()
                buf += chunk
                *lines, buf = buf.split("\n")
                for line in lines:
                    if line.strip():
                        if idx >= after:
                            yield {"event": "ev", "id": str(idx), "data": line}
                        idx += 1
            await asyncio.sleep(0.25)

    async def replayed():
        evs = [json.loads(x) for x in path.read_text(encoding="utf8").splitlines() if x.strip()] if path.exists() else []
        prev = None
        for i, e in enumerate(evs):
            if await request.is_disconnected():
                return
            if prev is not None:
                await asyncio.sleep(min(max(e["ts"] - prev, 0) / max(speed, 0.1), 2.5))
            prev = e["ts"]
            yield {"event": "ev", "id": str(i), "data": json.dumps({**e, "replay": True})}
        yield {"event": "replay_end", "data": "{}"}

    return EventSourceResponse(replayed() if replay else live(), ping=15)


# ---- artifacts and views ---------------------------------------------------------------------------
def _light(m: dict) -> dict:
    s = m.get("summary")
    return {k: m.get(k) for k in ("id", "kind", "title", "description", "producer", "inputs", "status", "version",
                                  "parent", "source_dir", "created_at")} | {
        "one_line": s if isinstance(s, str) else (s or {}).get("one_line", "")}


@app.get("/api/sessions/{sid}/artifacts")
def artifacts(sid: str):
    return [_light(m) for m in handle(sid).session.ws.list()]


@app.get("/api/sessions/{sid}/artifacts/{aid}")
def artifact(sid: str, aid: str):
    try:
        m = handle(sid).session.ws.get(aid)
    except KeyError:
        raise HTTPException(404, "no such artifact") from None
    s = m.get("summary")
    return {**_light(m), "summary_text": s if isinstance(s, str) else (s or {}).get("text", ""), "code": m.get("code"),
            "reviews": [{k: v for k, v in r.items() if k != "report"} for r in m.get("reviews", [])]}


@app.get("/api/sessions/{sid}/artifacts/{aid}/data")
def artifact_data(sid: str, aid: str):
    try:
        return JSONResponse(handle(sid).session.ws.data_for_browser(aid))
    except KeyError:
        raise HTTPException(404, "no such artifact") from None


@app.get("/api/sessions/{sid}/artifacts/{aid}/module.js")
def artifact_module(sid: str, aid: str):
    p = _ws_dir(sid) / "artifacts" / aid / "module.js"
    if not p.exists():
        raise HTTPException(404, "no module")
    return Response(p.read_text(), media_type="application/javascript")


@app.get("/api/sessions/{sid}/artifacts/{aid}/viz.json")
def artifact_manifest(sid: str, aid: str):
    return handle(sid).session.ws.load_manifest(aid)


@app.get("/api/sessions/{sid}/artifacts/{aid}/shots/{name}")
def artifact_shot(sid: str, aid: str, name: str):
    p = _ws_dir(sid) / "artifacts" / aid / "shots" / Path(name).name
    if not p.exists():
        raise HTTPException(404, "no screenshot")
    return FileResponse(p, media_type="image/png")


@app.get("/api/sessions/{sid}/artifacts/{aid}/versions")
def viz_versions(sid: str, aid: str):
    ws = handle(sid).session.ws
    src = ws.get(aid).get("source_dir")
    vs = [m for m in ws.list() if m["kind"] == "viz" and m.get("source_dir") == src]
    return [_light(m) for m in sorted(vs, key=lambda m: m.get("version", 0))]


class ViewUpdate(BaseModel):
    params: dict | None = None
    viz: str | None = None


@app.post("/api/sessions/{sid}/views/{view_id}")
def update_view(sid: str, view_id: str, body: ViewUpdate):
    """User-driven view changes (no LLM): parameter values from the controls, switching versions / undo."""
    s = handle(sid).session
    with _views_lock:
        return _update_view(s, view_id, body)


def _update_view(s, view_id: str, body: "ViewUpdate"):
    views = s.ws.views()
    v = next((x for x in views["views"] if x["view_id"] == view_id), None)
    if not v:
        raise HTTPException(404, "no such view")
    if body.params:
        v["params"].update(body.params)
        s.events.emit("user", "view", action="params", view_id=view_id, params=body.params)
    if body.viz and body.viz != v["viz"]:
        meta = s.ws.get(body.viz)
        if meta.get("kind") != "viz" or meta.get("status") not in ("approved", "approved_with_issues"):
            raise HTTPException(400, "only approved visualizations can be shown")
        v.setdefault("history", []).append(v["viz"])
        v["viz"] = body.viz
        s.events.emit("user", "view", action="replace", view_id=view_id, viz=body.viz, previous=v["history"][-1])
    s.ws.save_views(views)
    return v


class SelectionIn(BaseModel):
    view_id: str | None = None
    viz: str | None = None
    items: list[dict] = []


@app.post("/api/sessions/{sid}/selection")
def set_selection(sid: str, body: SelectionIn):
    """Selections made in views are logged so the Lead and replay mode can see them."""
    s = handle(sid).session
    s.ws.update_views(lambda views: views.__setitem__("selection", body.model_dump()))
    s.events.emit("user", "select", view_id=body.view_id, viz=body.viz, items=body.items[:200])
    return {"ok": True}


@app.get("/api/entity/{eid}")
def entity(eid: str):
    r = dataset.entity(eid)
    if not r:
        raise HTTPException(404, "unknown id")
    return JSONResponse(json.loads(json.dumps(r, default=str)))


# ---- runtime page for views (rendered inside sandboxed iframes) -----------------------------------
@app.get("/runtime/view.html")
def view_page(request: Request, session: str, viz: str, view: str = "", w: int = 900, h: int = 600,
              mode: str = "light", fresh: bool = False):
    """`fresh=1`: start from the manifest defaults; the UI then pushes the parameter values it derived from the
    event stream (this keeps replays faithful to the moment being replayed)."""
    s = handle(session).session
    manifest = s.ws.load_manifest(viz)
    if not manifest:
        raise HTTPException(404, "no such visualization")
    params = {k: sch.get("default") for k, sch in ((manifest.get("params") or {}).get("properties") or {}).items()}
    v = next((x for x in s.ws.views()["views"] if x["view_id"] == view), None)
    if v and not fresh:
        params.update(v.get("params") or {})
    base = str(request.base_url).rstrip("/")
    cfg = {"moduleUrl": f"{base}/api/sessions/{session}/artifacts/{viz}/module.js",
           "themeUrl": f"{base}/runtime/theme.json",
           "dataUrls": {n: f"{base}/api/sessions/{session}/artifacts/{a}/data" for n, a in manifest["data"].items()},
           "params": params, "width": max(w, 200), "height": max(h, 150), "mode": mode, "viewId": view or viz}
    html = (STATIC / "host.html").read_text().replace(
        '<script type="module" src="./host.js"></script>',
        f"<script>window.__SCIVIZ_CONFIG__ = {json.dumps(cfg)};</script>\n"
        f'<script type="module" src="{base}/runtime/host.js"></script>')
    return HTMLResponse(html)


@app.get("/runtime/{name}")
def runtime_file(name: str):
    p = STATIC / Path(name).name
    if not p.exists():
        raise HTTPException(404)
    media = "application/javascript" if p.suffix == ".js" else ("application/json" if p.suffix == ".json" else None)
    return FileResponse(p, media_type=media)


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="ui")
