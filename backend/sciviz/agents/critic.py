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
