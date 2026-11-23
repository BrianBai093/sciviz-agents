"""Visualization tools: headless preview and the verification gate (PLAN §3.5, DECISIONS D9).

The gate is enforced here, not by prompting: a view only becomes `approved` after automated render and
interaction checks pass and the independent Critic accepts it. After repeated failures the Viz agent is
escalated to the stronger model for one more round; after that the best version is delivered with its
remaining issues flagged.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from langchain_core.tools import tool

from ..agents import critic
from ..config import settings
from ..runtime.cdn import ImportError_, pin_imports
from ..runtime.renderer import RenderReport, render_viz
from ..session import Session
from .data_tools import _emit_call, _emit_result


class VizSourceError(ValueError):
    pass


def load_source(s: Session, slug: str) -> tuple[str, dict, dict, list]:
    """Read and validate viz/<slug>/{module.js, viz.json}; returns pinned code, manifest, data, libraries."""
    d = s.ws.root / "viz" / slug
    mod, man = d / "module.js", d / "viz.json"
    if not mod.exists() or not man.exists():
        raise VizSourceError(f"expected /viz/{slug}/module.js and /viz/{slug}/viz.json (write them with write_file)")
    try:
        manifest = json.loads(man.read_text())
    except json.JSONDecodeError as e:
        raise VizSourceError(f"viz.json is not valid JSON: {e}") from None
    problems = []
    if not manifest.get("title"):
        problems.append("viz.json needs a 'title'")
    bindings = manifest.get("data")
    if not isinstance(bindings, dict) or not bindings:
        problems.append("viz.json needs 'data': {binding_name: artifact_id}")
        bindings = {}
    params = manifest.get("params")
    if params is not None and not (isinstance(params, dict) and isinstance(params.get("properties", {}), dict)):
        problems.append("viz.json 'params' must be a JSON Schema object with 'properties'")
    data, size = {}, 0
    for name, aid in bindings.items():
        try:
            meta = s.ws.get(aid)
        except KeyError:
            problems.append(f"data binding '{name}' points to unknown artifact {aid}")
            continue
        if meta["kind"] == "viz":
            problems.append(f"data binding '{name}' points to a visualization ({aid}); bind data artifacts")
            continue
        data[name] = s.ws.data_for_browser(aid)
        size += len(json.dumps(data[name], default=str))
    if size > settings.max_view_data_mb * 1e6:
        problems.append(f"bound data is {size / 1e6:.1f} MB; the limit per view is {settings.max_view_data_mb} MB "
                        "(aggregate, filter or sample the data first)")
    if problems:
        raise VizSourceError("; ".join(problems))
    code = mod.read_text()
    syntax = _syntax_error(code)
    if syntax:
        raise VizSourceError(f"JavaScript syntax error: {syntax}")
    try:
        pinned, libs = pin_imports(code)
    except ImportError_ as e:
        raise VizSourceError(f"import problem: {e}") from None
    manifest["libraries"] = [{"name": lib.name, "version": lib.version, "url": lib.url} for lib in libs]
    return pinned, manifest, data, manifest["libraries"]


def _syntax_error(code: str) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
        f.write(code)
    r = subprocess.run([node, "--check", f.name], capture_output=True, text=True, timeout=30)
    Path(f.name).unlink(missing_ok=True)
    return None if r.returncode == 0 else "\n".join(r.stderr.strip().splitlines()[-6:])


def _data_summary(s: Session, manifest: dict) -> str:
    parts = []
    for name, aid in manifest.get("data", {}).items():
        try:
            parts.append(f"[{name}] " + s.ws.describe(aid)[:1800])
        except KeyError:
            pass
    return "\n\n".join(parts)


def viz_tools(s: Session, agent: str):
    @tool
    def render_preview(slug: str, params: dict | None = None) -> str:
        """Render /viz/<slug>/module.js headlessly (same runtime as the UI) and run the automated checks:
        errors, layout metrics and interaction tests. Saves screenshots you can look at with read_file.
        Use this to debug before submit_viz. Optional `params` overrides parameter values."""
        _emit_call(s, agent, "render_preview", {"slug": slug, "params": params})
        try:
            code, manifest, data, libs = load_source(s, slug)
        except VizSourceError as e:
            text = f"Cannot render: {e}"
            _emit_result(s, agent, "render_preview", False, text)
            return text
        out = s.ws.root / "viz" / slug / "preview"
        rep = render_viz(code, data, out, params=params, params_schema=manifest.get("params"))
        shots = ", ".join(f"/viz/{slug}/preview/{Path(p).name}" for p in rep.screenshots.values())
        text = (f"{rep.text()}\nlibraries: {[f'{x['name']}@{x['version']}' for x in libs]}\n"
                f"screenshots: {shots} (open them with read_file to see the view)")
        _emit_result(s, agent, "render_preview", rep.ok, text)
        return text

    @tool
    def submit_viz(slug: str, acceptance_criteria: str = "") -> str:
        """Submit /viz/<slug> to the verification gate: automated render + interaction checks, then an independent
        critic reviews screenshots. Returns APPROVED (done), REVISE (fix the listed issues and submit again)
        or STOP (no more attempts; report the outcome). Pass the acceptance criteria from your brief."""
        _emit_call(s, agent, "submit_viz", {"slug": slug, "acceptance_criteria": acceptance_criteria})
        g = s.gate(slug)
        try:
            code, manifest, data, libs = load_source(s, slug)
        except VizSourceError as e:
            g.failures += 1
            text = _after_failure(s, g, slug, f"Source problem: {e}")
            _emit_result(s, agent, "submit_viz", False, text)
            return text
        meta = s.ws.register_viz(slug, manifest["title"], producer=agent,
                                 inputs=list(manifest["data"].values()), parent=g.last_artifact,
                                 manifest=manifest, module_code=code)
        aid = meta["id"]
        g.last_artifact = aid
        s.events.emit(agent, "artifact", id=aid, artifact_kind="viz", title=manifest["title"], version=meta["version"])
        shots_dir = s.ws.artifact_dir(aid) / "shots"
        rep: RenderReport = render_viz(code, data, shots_dir, params_schema=manifest.get("params"))
        automated = rep.text()
        auto_problems = []
        if not rep.ok:
            auto_problems.append("the view does not render cleanly (see errors above)")
        auto_problems += [f"interaction test '{t['name']}' failed: {t['detail']}" for t in rep.interaction_failures]
        review = {"stage": "automated", "report": rep.to_dict()}
        if auto_problems:
            s.ws.update_meta(aid, status="rejected", reviews=[review])
            g.failures += 1
            s.events.emit("gate", "gate", artifact=aid, verdict="revise", stage="automated", problems=auto_problems,
                          screenshot=rep.screenshots.get("default"))
            text = _after_failure(s, g, slug, f"{aid} failed automated checks:\n" + automated, artifact=aid,
                                  render_ok=rep.ok)
            _emit_result(s, agent, "submit_viz", False, text)
            return text
        verdict = critic.review(s.user_question, acceptance_criteria, manifest["title"],
                                manifest.get("description", ""), automated, _data_summary(s, manifest),
                                rep.screenshots, params_schema=manifest.get("params"),
                                callbacks=[s.usage_callback])
        review_c = {"stage": "critic", **verdict.model_dump()}
        issues = "\n".join(f"- [{i.severity}] {i.problem} -> {i.fix}" for i in verdict.issues) or "- none"
        scores = (f"answers_question {verdict.answers_question}/5, truthfulness {verdict.truthfulness}/5, "
                  f"readability {verdict.readability}/5, interaction {verdict.interaction}/5")
        s.events.emit("critic", "gate", artifact=aid, verdict=verdict.verdict, scores=scores,
                      summary=verdict.summary, issues=[i.model_dump() for i in verdict.issues],
                      screenshot=rep.screenshots.get("default"))
        if verdict.verdict == "pass":
            s.ws.update_meta(aid, status="approved", reviews=[review, review_c])
            s.escalate_agents.discard(agent)
            text = (f"APPROVED as {aid} (version {meta['version']}). Critic: {scores}. {verdict.summary}\n"
                    f"Remaining minor issues:\n{issues}\nReport back to the lead now.")
            _emit_result(s, agent, "submit_viz", True, text)
            return text
        s.ws.update_meta(aid, status="rejected", reviews=[review, review_c])
        g.failures += 1
        text = _after_failure(s, g, slug, f"{aid} was reviewed by the critic: REVISE.\nScores: {scores}\n"
                                           f"Summary: {verdict.summary}\nIssues:\n{issues}", artifact=aid, render_ok=True)
        _emit_result(s, agent, "submit_viz", False, text)
        return text

    def _after_failure(s: Session, g, slug: str, details: str, artifact: str | None = None,
                       render_ok: bool = False) -> str:
        limit = settings.max_gate_revisions
        if g.failures < limit:
            return f"REVISE (attempt {g.failures} of {limit}).\n{details}\nFix these issues, then call submit_viz again."
        if not g.escalated:
            g.escalated = True
            s.escalate_agents.add(agent)
            s.events.emit("gate", "plan", escalation=f"{agent} escalated to {settings.escalation_model}")
            return (f"REVISE (final attempt; you now run on a stronger model).\n{details}\n"
                    "Fix these issues carefully, then call submit_viz one last time.")
        s.escalate_agents.discard(agent)
        if artifact and render_ok:
            s.ws.update_meta(artifact, status="approved_with_issues")
            return (f"STOP. No attempts left. {artifact} is delivered with status approved_with_issues.\n{details}\n"
                    "Report the remaining issues to the lead.")
        return f"STOP. No attempts left and the view does not render.\n{details}\nReport the failure to the lead."

    return [render_preview, submit_viz]
