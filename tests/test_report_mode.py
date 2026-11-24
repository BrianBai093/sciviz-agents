"""Report mode (Project 2) harness pieces without LLM calls: report checks and HTML, figure file checks,
background jobs with the cell log, and export + offline replay of a run."""
import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import sciviz.harness.budget as budget_mod
import sciviz.session as session_mod
from sciviz.harness import report as rep
from sciviz.harness.export import export_run
from sciviz.tools.data_tools import python_tool
from sciviz.tools.figure_tools import check_files

REPO = Path(__file__).resolve().parents[1]
SAMPLE_DB = REPO / "catalog" / "columbia_sample.duckdb"

ARTS = {"T1": {"kind": "table", "title": "t", "description": "d", "summary": "s"},
        "F1": {"kind": "finding", "title": "f", "description": "", "summary": "s"},
        "P1": {"kind": "figure", "title": "Fig", "description": "cap", "summary": "s", "status": "approved"},
        "P2": {"kind": "figure", "title": "Draft", "description": "cap", "summary": "s", "status": "rejected"}}


def test_report_checks_catch_unsupported_numbers_and_bad_ids():
    md = "## Results\n\nThe mean fell by 12.5% across 4,210 works.\n\nSee [T9] and {{figure:P2}}.\n"
    problems = rep.check(md, ARTS)
    assert any("no citation" in p and "12.5%" in p for p in problems)
    assert any("T9 does not exist" in p for p in problems)
    assert any("P2 has not passed" in p for p in problems)


def test_report_checks_pass_with_citations_years_and_small_integers():
    md = ("## Results\n\nIn 2021 teams of 1 to 10 authors were compared; the mean fell by 12.5% [F1].\n\n"
          "{{figure:P1}}\n\n| size | mean |\n|---|---|\n| 1 | 0.31 |\n\nTable values come from [T1].\n\n"
          "The original study used 24 million papers [brief]; claim C1 is tested in Figure P1.\n")
    assert rep.check(md, ARTS) == []
    html = rep.to_html("# Title\n\n" + md, ARTS, Path("/tmp"))
    assert "<b>Figure 1.</b>" in html and "tested in Figure 1." in html and 'class="cite">[F1]' in html and "Evidence index" in html


def test_figure_file_checks(tmp_path):
    pdf, png = tmp_path / "f.pdf", tmp_path / "f.png"
    assert len(check_files(pdf, png)) == 2
    pdf.write_bytes(b"%PDF-1.4 minimal")
    Image.fromarray(np.full((600, 1000), 255, dtype=np.uint8)).save(png)
    assert any("blank" in p for p in check_files(pdf, png))
    arr = np.random.default_rng(0).integers(0, 255, (600, 1000), dtype=np.uint8)
    Image.fromarray(arr).save(png)
    assert check_files(pdf, png) == []


@pytest.fixture()
def session(tmp_path, monkeypatch):
    s = dataclasses.replace(session_mod.settings, workspaces_dir=tmp_path / "ws", db_path=SAMPLE_DB)
    for mod in (session_mod, budget_mod):
        monkeypatch.setattr(mod, "settings", s)
    sess = session_mod.Session("report-test")
    yield sess
    sess.close()


def test_job_cells_export_and_offline_replay(session, tmp_path):
    run_python = python_tool(session, "analyst")
    run_python.invoke({"code": "df = sql('select 1 as x union all select 2'); save_table(df, 'two rows')"})
    run_python.invoke({"code": "helper = lambda d: int(d.x.sum())"})
    run_python.invoke({"code": "raise ValueError('an expected failure')"})
    run_python.invoke({"code": "save_json({'total': helper(load('T1'))}, 'json', 'total')"})
    job = session.jobs.start("analyst", "squares", "t = load('T1'); t['sq'] = t.x ** 2; save_table(t, 'squares')\n"
                             "print('done')")
    job = session.jobs.wait(job.id, 60)
    assert job.returncode == 0 and job.created == ["T2"]
    assert session.ws.get("T2")["code"].startswith("t = load('T1')")
    log = [json.loads(x) for x in (session.ws.root / "kernel_log.jsonl").read_text().splitlines()]
    assert [c["ok"] for c in log] == [True, True, False, True, True] and log[-1]["job"] == "job1"

    out = tmp_path / "pkg"
    summary = export_run(session.ws.root, out, tmp_path / "no_cache.sqlite")
    assert summary["cells"] == 5 and summary["artifacts"] == 3
    r = subprocess.run([sys.executable, str(out / "scripts" / "run_all.py"), "--db", str(SAMPLE_DB)],
                       capture_output=True, text=True, timeout=300, cwd=REPO)
    assert r.returncode == 0, r.stderr[-2000:]
    assert "Artifacts identical: 3; different: 0 []; not recreated: 0 []" in r.stdout, r.stdout[-2000:]
    assert "differs from the original run" not in r.stdout


def test_render_pdf(tmp_path):
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
    except Exception:
        pytest.skip("Chromium is not installed")
    rep.render_pdf(rep.to_html("# T\n\n## A\n\nText [brief].\n", {}, tmp_path), tmp_path / "r.html", tmp_path / "r.pdf")
    assert (tmp_path / "r.pdf").read_bytes()[:5] == b"%PDF-"
