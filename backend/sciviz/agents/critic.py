"""Critic: an independent reviewer that sees screenshots, automated check results and data summaries.

It never sees the Viz agent's reasoning or code, so it cannot be argued into approving a weak view.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .models import make_llm

# The shared rules for reader-facing text (also given to the writer and the analyst).
PLAIN_LANGUAGE = (Path(__file__).resolve().parent.parent / "prompts" / "plain_language.md").read_text().strip()

CRITIC_PROMPT = """You are an independent reviewer of interactive data visualizations. You did not build the view you are
reviewing. Judge it from the screenshots, the automated check results and the data summary.

Criteria (score each 1-5):
1. answers_question: the view shows what the user asked for and meets the acceptance criteria.
2. truthfulness: encodings are not misleading (scales, baselines, aggregation, color), titles and labels match the
   data, and values are plausible given the data summary.
3. readability: labels are legible, clutter or occlusion does not hide the answer, legends and axes exist where
   needed, color use is sensible, the view fits its frame.
4. interaction: data marks respond to hover and selection (see the automated tests) and selection/highlight
   is clearly visible.

The host application renders controls for the view's declared parameters next to the view (they are not part of
the screenshots); do not penalize the absence of in-view widgets for declared parameters. Judge only whether the
declared parameters are meaningful for the task.

Review this one view in isolation, from what the screenshots and the automated checks show. Placing views next to each
other, linking selections between views, and other screen sizes are handled by the host application and are not part of
this review. Do not reject a view for lacking evidence this review process cannot provide (for example proofs of exact
algorithmic routing, other viewport sizes, or comparisons with other views); judge plausibility from what you can see.
Ignore acceptance criteria that cannot be checked from a single view.

Return verdict "pass" when a researcher could use the view as is (list remaining polish items as minor issues).
Return "revise" when any criterion scores 2 or lower or a major issue exists, and give concrete, actionable fixes.
Ask for a different technique only if the current one fails the question or readability badly."""


class Issue(BaseModel):
    severity: Literal["major", "minor"]
    problem: str
    fix: str


class Verdict(BaseModel):
    verdict: Literal["pass", "revise"]
    answers_question: int = Field(ge=1, le=5)
    truthfulness: int = Field(ge=1, le=5)
    readability: int = Field(ge=1, le=5)
    interaction: int = Field(ge=1, le=5)
    issues: list[Issue] = Field(default_factory=list)
    summary: str


def _img(path: str) -> dict:
    return {"type": "image", "base64": base64.b64encode(Path(path).read_bytes()).decode(), "mime_type": "image/png"}


def review(question: str, criteria: str, title: str, description: str, report_text: str, data_summary: str,
           screenshots: dict[str, str], params_schema: dict | None = None, callbacks=None) -> Verdict:
    props = (params_schema or {}).get("properties", {}) if isinstance(params_schema, dict) else {}
    params_text = "\n".join(f"- {k}: {v.get('title', '')} (default {v.get('default')!r})" for k, v in props.items()) \
        or "(none)"
    content: list[dict] = [{"type": "text", "text": (
        f"USER QUESTION:\n{question}\n\nACCEPTANCE CRITERIA:\n{criteria or '(none given)'}\n\n"
        f"VIEW TITLE: {title}\nDESCRIPTION (by its author): {description}\n\n"
        f"DECLARED PARAMETERS (controls rendered by the host app, outside the screenshots):\n{params_text}\n\n"
        f"AUTOMATED CHECKS:\n{report_text}\n\nDATA BOUND TO THE VIEW:\n{data_summary}\n\n"
        "Screenshots follow: the default state, then the state after clicking one data mark (selection).")}]
    for name in ("default", "selected"):
        if name in screenshots:
            content.append({"type": "text", "text": f"[{name}]"})
            content.append(_img(screenshots[name]))
    llm = make_llm("critic").with_structured_output(Verdict)
    return llm.invoke([SystemMessage(CRITIC_PROMPT), HumanMessage(content=content)],
                      config={"callbacks": callbacks or [], "metadata": {"sciviz_agent": "critic"}})


# ---- report mode (Project 2): static figures and report text --------------------------------------------
FIGURE_CRITIC_PROMPT = """You are an independent reviewer of figures for a research report. You did not make the figure.
Judge it from the image, its caption, the claims it is meant to support, and the summaries of the data behind it.

Criteria (score each 1-5):
1. supports_claims: the figure shows the evidence needed to judge the listed claims, at the right level (groups,
   measures, comparisons), without leaving out what a reader needs. Score whether the figure tests the claims, not
   whether the claims hold: a figure showing that a claim held only in part, or not at all, serves the report as
   well as one confirming it, provided the caption says what it shows. The claims are the study's and their wording
   is not part of this review.
2. truthfulness: axes, scales, baselines, units and labels are correct and not misleading; uncertainty (for example
   confidence intervals) and sample sizes are shown or stated where the claim depends on them; values are plausible
   given the data summaries.
3. readability: legible at print size (two-column paper width), no overlapping text, legends and axis titles
   present, sensible colors (distinguishable, also for color-blind readers), uncluttered.
4. caption: the title says in plain words what the figure shows; the caption says what is plotted, the data and
   sample, how uncertainty is shown and what to look at. Title, caption, axis labels and legends follow the plain-
   language rules below: a reader of the report sees only the figure and its caption, so labels, abbreviations,
   symbols or version names that the authors made up are a major issue.

Return verdict "pass" when the figure could go into the report as is (list remaining polish items as minor issues).
Return "revise" when any criterion scores 2 or lower or a major issue exists, and give concrete, actionable fixes.
Do not ask for analyses beyond the figure's purpose.

""" + PLAIN_LANGUAGE


class FigureVerdict(BaseModel):
    verdict: Literal["pass", "revise"]
    supports_claims: int = Field(ge=1, le=5)
    truthfulness: int = Field(ge=1, le=5)
    readability: int = Field(ge=1, le=5)
    caption: int = Field(ge=1, le=5)
    issues: list[Issue] = Field(default_factory=list)
    summary: str


def review_figure(question: str, claims_text: str, title: str, caption: str, data_summary: str, png: str,
                  callbacks=None) -> FigureVerdict:
    content: list[dict] = [{"type": "text", "text": (
        f"RESEARCH QUESTION:\n{question}\n\nCLAIMS THIS FIGURE SUPPORTS:\n{claims_text}\n\n"
        f"FIGURE TITLE: {title}\nCAPTION (by its author): {caption}\n\nDATA BEHIND THE FIGURE:\n{data_summary}\n\n"
        "The figure follows.")}, _img(png)]
    llm = make_llm("critic").with_structured_output(FigureVerdict)
    return llm.invoke([SystemMessage(FIGURE_CRITIC_PROMPT), HumanMessage(content=content)],
                      config={"callbacks": callbacks or [], "metadata": {"sciviz_agent": "critic"}})


REPORT_REVIEWER_PROMPT = """You are an independent reviewer of a reproduction report. A team tried to reproduce a published
study on a different dataset. You did not write the report. You get the paper brief (the study's claims), the team's
claim plan, the report text, and the evidence: every finding the team recorded and a summary of every artifact.

Check:
1. support: every number and factual statement in the report is backed by the cited evidence, and the cited numbers
   match the findings (allow rounding); statements about the original study (its authors, data, methods and
   results) match the paper brief and add nothing it does not say;
2. coverage: every claim in the claim plan is addressed, with a clear status (reproduced / partly / not reproduced /
   not testable) and the reason;
3. honesty: conclusions follow from the evidence; no overclaiming (causal language, generalizing beyond the data,
   hiding null or opposite results); deviations from the study's method and the data's limitations are stated;
4. clarity: a reader can tell the question, the data, the method, the results and the answer.

Return verdict "pass" when the report can be released as is (list remaining polish items as minor issues).
Return "revise" for any unsupported or mismatched number, a missing claim, or overclaiming, with concrete fixes
(quote the sentence to change)."""


class ReportVerdict(BaseModel):
    verdict: Literal["pass", "revise"]
    support: int = Field(ge=1, le=5)
    coverage: int = Field(ge=1, le=5)
    honesty: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    issues: list[Issue] = Field(default_factory=list)
    summary: str


def review_report(brief: str, claim_plan: str, report_md: str, evidence: str, callbacks=None) -> ReportVerdict:
    text = (f"PAPER BRIEF:\n{brief}\n\nCLAIM PLAN:\n{claim_plan}\n\nREPORT (Markdown):\n{report_md}\n\n"
            f"EVIDENCE (findings and artifact summaries):\n{evidence}")
    llm = make_llm("critic").with_structured_output(ReportVerdict)
    return llm.invoke([SystemMessage(REPORT_REVIEWER_PROMPT), HumanMessage(content=text)],
                      config={"callbacks": callbacks or [], "metadata": {"sciviz_agent": "reviewer"}})


COLD_READER_PROMPT = """You are a careful reader of a research report: a researcher from a neighbouring field who has
not seen the work behind it. You get only the report. Each figure appears where it stands as its number, title and
caption in square brackets; the captions were reviewed with the figures, so read them for context and do not list
problems in them. Citations in square brackets (for example [T3] or [brief]) point to the authors' evidence; ignore
them.

Read the main text (every section before the appendix) as a whole and find what would stop you from following it
on a first reading:
- words, labels, abbreviations or symbols that the authors seem to have made up, or that are used before or
  without an explanation;
- sentences you would have to read twice;
- passages about the history of the work (earlier versions, stages, corrections) that a reader does not need;
- a method or result whose meaning you cannot tell from the text.
Sections titled "Appendix" are for specialists: check them only for labels the authors made up.

List at most 12 problems, the most important first. For each, quote the exact words and give plain wording that
keeps the meaning and every number; prefer fixes that make the text shorter or simpler over fixes that add
explanation. Mark a problem "major" only when it keeps a reader from understanding a main method or result, or when
it is a label the authors made up; mark everything else "minor". Score readability 1-5 (5: a researcher from a
neighbouring field follows the main text on a first reading). Return "pass" when no major problem remains.

The authors were asked to follow these rules:

""" + PLAIN_LANGUAGE


class ReadabilityVerdict(BaseModel):
    verdict: Literal["pass", "revise"]
    readability: int = Field(ge=1, le=5)
    issues: list[Issue] = Field(default_factory=list)
    summary: str


def review_readability(reader_text: str, callbacks=None) -> ReadabilityVerdict:
    """The report gate's second check: a reader who sees only the report (not the evidence, the claim plan or the
    team's vocabulary) lists what they cannot follow."""
    llm = make_llm("critic").with_structured_output(ReadabilityVerdict)
    return llm.invoke([SystemMessage(COLD_READER_PROMPT), HumanMessage(content=f"REPORT:\n{reader_text}")],
                      config={"callbacks": callbacks or [], "metadata": {"sciviz_agent": "critic"}})
