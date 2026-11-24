"""Report tools (report mode): the Writer writes sections; `submit_report` is the report gate.

The gate is enforced here: mechanical evidence checks first, then an independent reviewer, then rendering.
After `REPORT_ROUNDS` reviewed submissions the latest version is released with the open review issues appended.
"""
from __future__ import annotations

import json
import re

from langchain_core.tools import tool

from ..agents import critic
from ..harness import report as rep
from ..session import Session
from .data_tools import _emit_call, _emit_result

REPORT_ROUNDS = 3


def _artifacts(s: Session) -> dict[str, dict]:
    return {m["id"]: m for m in s.ws.list()}


def report_tools(s: Session, agent: str):
    @tool
    def write_section(position: int, name: str, markdown: str) -> str:
        """Write (or overwrite) one report section. `position` orders sections (1, 2, ...); `name` is a short
        lowercase slug (e.g. "methods"). Start the Markdown with a level-2 heading ("## Methods"). Cite evidence as
        [T3] or [F2, T5] (artifact ids) and facts about the original study as [brief]. Place a figure with
        {{figure:<figure artifact id>}} on its own line; refer to it in text as "Figure <id>" (numbers are assigned
        when the report is built). Tables are Markdown tables. Write formulas in plain text, without LaTeX."""
        slug = re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-") or "section"
        d = rep.sections_dir(s.ws.root)
        for old in d.glob(f"*_{slug}.md"):
            old.unlink()
        path = d / f"{int(position):02d}_{slug}.md"
        path.write_text(markdown.strip() + "\n", encoding="utf8")
        s.events.emit(agent, "tool_call", tool="write_section", args={"name": slug, "position": position})
        problems = rep.check(markdown, _artifacts(s))
        note = ("\nChecks on this section:\n- " + "\n- ".join(problems)) if problems else " Checks passed."
        return f"Saved section {path.name} ({len(markdown)} characters).{note}"

    @tool
    def read_report_draft() -> str:
        """The current assembled draft (all sections in order) and the list of section files."""
        secs = rep.list_sections(s.ws.root)
        names = ", ".join(p.name for _, _, p in secs) or "(none)"
        return f"Sections: {names}\n\n" + rep.assemble(s.ws.root, "(title set at submission)")

    @tool
    def submit_report(title: str, subtitle: str = "") -> str:
        """Submit the assembled report to the report gate: mechanical checks (cited ids exist, figures are
        approved, statistics carry citations), then an independent reviewer. On "pass" (or after the last round)
        the report is rendered to report/report.pdf. Returns the verdict and, on "revise", the issues to fix."""
        _emit_call(s, agent, "submit_report", {"title": title})
        arts = _artifacts(s)
        md = rep.assemble(s.ws.root, title)
        if not rep.list_sections(s.ws.root):
            return "No sections written yet."
        problems = rep.check(md, arts)
        if problems:
            text = "Not submitted; fix these first:\n- " + "\n- ".join(problems)
            _emit_result(s, agent, "submit_report", False, text)
            return text
        gate = s.gate("report")
        brief_file = s.ws.root / "inputs" / "paper_brief.md"
        brief = brief_file.read_text(encoding="utf8") if brief_file.exists() else "(no brief)"
        plan_file = s.ws.root / "claim_plan.json"
        plan = plan_file.read_text(encoding="utf8") if plan_file.exists() else "(no claim plan)"
        verdict = critic.review_report(brief, plan, md, rep.evidence_text(arts, s.ws.root),
                                       callbacks=[s.usage_callback])
        scores = {k: getattr(verdict, k) for k in ("support", "coverage", "honesty", "clarity")}
        round_no = gate.failures + 1
        issues = "\n".join(f"- [{i.severity}] {i.problem} -> fix: {i.fix}" for i in verdict.issues) or "- none"
        review_log = s.ws.root / "report" / "reviews.jsonl"
        with review_log.open("a", encoding="utf8") as f:
            f.write(json.dumps({"round": round_no, "verdict": verdict.verdict, "scores": scores,
                                "summary": verdict.summary, "issues": [i.model_dump() for i in verdict.issues]}) + "\n")
        s.events.emit("critic", "gate", artifact="report", verdict=verdict.verdict, stage="report review",
                      scores=scores, summary=verdict.summary,
                      problems=[i.problem for i in verdict.issues if i.severity == "major"])
        if verdict.verdict != "pass" and round_no < REPORT_ROUNDS:
            gate.failures += 1
            text = (f"Report needs revision (round {round_no} of {REPORT_ROUNDS}): {verdict.summary}\n{issues}\n"
                    "Revise the sections, then submit again.")
            _emit_result(s, agent, "submit_report", False, text)
            return text
        status = "approved" if verdict.verdict == "pass" else "approved_with_issues"
        if status == "approved_with_issues":
            open_items = [i for i in verdict.issues if i.severity == "major"] or verdict.issues
            md += ("\n## Open review issues\n\nThe independent review still raised these points after "
                   f"{REPORT_ROUNDS} rounds:\n\n" + "\n".join(f"- {i.problem}" for i in open_items) + "\n")
        out = s.ws.root / "report"
        (out / "report.md").write_text(md, encoding="utf8")
        html_text = rep.to_html(md, arts, s.ws.root, subtitle)
        rep.render_pdf(html_text, out / "report.html", out / "report.pdf")
        (out / "status.json").write_text(json.dumps({"status": status, "round": round_no, "scores": scores,
                                                     "title": title, "subtitle": subtitle}))
        s.events.emit(agent, "report", status=status, pdf=str(out / "report.pdf"))
        text = (f"Report {status} in round {round_no} ({scores}); rendered to report/report.pdf.\n"
                f"Reviewer summary: {verdict.summary}\nRemaining issues:\n{issues}")
        _emit_result(s, agent, "submit_report", True, text)
        return text

    return [write_section, read_report_draft, submit_report]
