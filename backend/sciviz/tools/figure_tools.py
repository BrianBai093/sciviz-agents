"""Figure gate (report mode, PLAN_P2 §3.3): a static figure enters the report only after automated checks and an
independent vision review. Enforced here, not by prompting. After `max_gate_revisions` failed rounds the latest
version is accepted as `approved_with_issues`, and its open issues travel with it."""
from __future__ import annotations

import json

import numpy as np
from langchain_core.tools import tool
from PIL import Image

from ..agents import critic
from ..config import settings
from ..session import Session
from .data_tools import _emit_call, _emit_result


def check_files(pdf, png) -> list[str]:
    problems = []
    if not pdf.exists() or pdf.read_bytes()[:5] != b"%PDF-":
        problems.append(f"missing or invalid PDF at {pdf.name} (save with fig.savefig(path) and a .pdf suffix)")
    if not png.exists():
        problems.append(f"missing PNG at {png.name} (save with fig.savefig(path, dpi=200))")
        return problems
    try:
        im = Image.open(png).convert("L")
    except Exception as e:
        return problems + [f"PNG cannot be read: {e}"]
    if im.width < 800:
        problems.append(f"PNG is {im.width}px wide; save at a higher dpi (at least 800px wide)")
    if float(np.asarray(im, dtype=float).std()) < 3:
        problems.append("PNG looks blank")
    return problems


def figure_tools(s: Session, agent: str):
    @tool
    def submit_figure(slug: str, title: str, caption: str, claim_ids: list[str], input_artifacts: list[str]) -> str:
        """Submit a finished figure to the review gate. Save it first from your kernel as BOTH
        `figures/<slug>.pdf` (vector) and `figures/<slug>.png` (dpi 200 or more), relative to the working directory.
        `caption`: what is plotted, the data and sample sizes, how uncertainty is shown. `claim_ids`: ids from the
        claim plan the figure supports. `input_artifacts`: the artifact ids whose data the figure shows.
        Returns the verdict; on "revise", fix the issues, re-save the files and submit again with the same slug."""
        _emit_call(s, agent, "submit_figure", {"slug": slug, "title": title, "claim_ids": claim_ids})
        folder = s.ws.root / "figures"
        pdf, png = folder / f"{slug}.pdf", folder / f"{slug}.png"
        problems = check_files(pdf, png)
        missing = [a for a in input_artifacts if a not in {m["id"] for m in s.ws.list()}]
        if missing:
            problems.append(f"unknown input artifacts: {missing}")
        if problems:
            text = "Not submitted: " + "; ".join(problems)
            _emit_result(s, agent, "submit_figure", False, text)
            return text
        gate = s.gate(f"figure:{slug}")
        meta = s.ws.register_figure(slug, title, caption, producer=agent, inputs=input_artifacts, claims=claim_ids,
                                    pdf=pdf, png=png, parent=gate.last_artifact)
        aid = meta["id"]
        gate.last_artifact = aid
        plan_file = s.ws.root / "claim_plan.json"
        claims = json.loads(plan_file.read_text())["claims"] if plan_file.exists() else []
        claims_text = "\n".join(f"{c['id']}: {c['claim']}" for c in claims if c["id"] in claim_ids) or "(none given)"
        data_summary = "\n\n".join(s.ws.describe(a)[:2500] for a in input_artifacts)
        verdict = critic.review_figure(s.user_question, claims_text, title, caption, data_summary,
                                       str(s.ws.artifact_dir(aid) / "figure.png"),
                                       callbacks=[s.usage_callback])
        scores = {k: getattr(verdict, k) for k in ("supports_claims", "truthfulness", "readability", "caption")}
        review = {"round": gate.failures + 1, "verdict": verdict.verdict, "scores": scores, "summary": verdict.summary,
                  "issues": [i.model_dump() for i in verdict.issues]}
        if verdict.verdict == "pass":
            status = "approved"
        elif gate.failures + 1 >= settings.max_gate_revisions:
            status = "approved_with_issues"
        else:
            status = "rejected"
            gate.failures += 1
        s.ws.update_meta(aid, status=status, reviews=[*s.ws.get(aid).get("reviews", []), review])
        s.events.emit("critic", "gate", artifact=aid, verdict=verdict.verdict, stage="figure review", scores=scores,
                      summary=verdict.summary, problems=[i.problem for i in verdict.issues if i.severity == "major"])
        issues = "\n".join(f"- [{i.severity}] {i.problem} -> fix: {i.fix}" for i in verdict.issues) or "- none"
        if status == "approved":
            text = f"{aid} approved ({scores}). {verdict.summary}\nMinor issues you may still fix:\n{issues}"
        elif status == "approved_with_issues":
            text = (f"{aid} accepted with open issues after {settings.max_gate_revisions} rounds; the report must "
                    f"mention them.\n{issues}")
        else:
            text = (f"{aid} needs revision (round {gate.failures} of {settings.max_gate_revisions}): "
                    f"{verdict.summary}\n{issues}\nRe-save figures/{slug}.pdf and .png, then submit again.")
        _emit_result(s, agent, "submit_figure", status != "rejected", text)
        return text

    return [submit_figure]
