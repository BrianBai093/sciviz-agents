"""Generalizability guard (PLAN §6): prompts and harness code must not contain technique-specific logic.

The test fails if any denylisted visualization/layout technique name appears in agent prompts or in the
harness source. Test fixtures are excluded on purpose (they exercise the runtime, they are not used by agents).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend" / "sciviz"
DENYLIST = [
    r"force[- ]directed", r"d3-force", r"forceSimulation", r"force layout", r"edge[- ]bundl", r"curveBundle",
    r"hierarchical edge", r"sankey", r"chord", r"treemap", r"sunburst", r"streamgraph", r"voronoi",
    r"arc diagram", r"circle packing", r"choropleth", r"beeswarm", r"parallel coordinates", r"node-link",
    r"bar chart", r"line chart", r"scatter ?plot", r"histogram", r"heat ?map", r"pie chart",
]


def _sources():
    for p in ROOT.rglob("*"):
        if p.suffix in {".py", ".md", ".js", ".html", ".json", ".yaml"} and p.is_file():
            yield p


def test_no_technique_specific_terms():
    hits = []
    for p in _sources():
        text = p.read_text(encoding="utf8", errors="ignore")
        for pat in DENYLIST:
            for m in re.finditer(pat, text, flags=re.I):
                line = text[: m.start()].count("\n") + 1
                hits.append(f"{p.relative_to(ROOT)}:{line}: '{m.group(0)}'")
    assert not hits, "technique-specific terms found:\n" + "\n".join(hits)


# Report mode (Project 2, PLAN_P2 §4): knowledge of the reproduced study reaches the agents only through the
# paper brief, never through prompts or harness code.
STUDY_DENYLIST = [r"disrupt", r"team[ _-]?size", r"\bn_[ijk]\b", r"sleeping beaut", r"consolidat", r"Evans",
                  r"Wu,? Wang", r"CD[ -]index"]


def test_no_study_specific_terms():
    hits = []
    for p in _sources():
        text = p.read_text(encoding="utf8", errors="ignore")
        for pat in STUDY_DENYLIST:
            for m in re.finditer(pat, text, flags=re.I):
                line = text[: m.start()].count("\n") + 1
                hits.append(f"{p.relative_to(ROOT)}:{line}: '{m.group(0)}'")
    assert not hits, "study-specific terms found:\n" + "\n".join(hits)
