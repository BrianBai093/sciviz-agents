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
from sciviz.harness.file_log import LoggedFilesystemBackend
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
    # a later cell reads the job's script, as agents do when they build on an earlier job
    run_python.invoke({"code": "from pathlib import Path\nsave_json({'n': len(Path('jobs/job1/script.py').read_text())}, "
                               "'json', 'script length')"})
    # a file written with the agents' file tool, then run by a cell
    backend = LoggedFilesystemBackend(session.ws.root)
    backend.write("/helper.py", "def plus(x):\n    return x + 1\n")
    backend.edit("/helper.py", "x + 1", "x + 2")
    run_python.invoke({"code": "exec(open('helper.py').read()); save_json({'v': plus(1)}, 'json', 'plus')"})
    # a cell that depends on the original environment: in the replay it fails and its artifact is taken over
    run_python.invoke({"code": "import os\nassert os.environ['SCIVIZ_WORKSPACE'].endswith('report-test')\n"
                               "save_json({'ws': 1}, 'json', 'environment check')"})
    run_python.invoke({"code": "save_json({'again': load('J4')['ws']}, 'json', 'uses the check')"})
    log = [json.loads(x) for x in (session.ws.root / "kernel_log.jsonl").read_text().splitlines()]
    assert [c["ok"] for c in log] == [True, True, False, True, True, True, True, True, True]
    assert log[4]["job"] == "job1"
    assert [json.loads(x)["op"] for x in (session.ws.root / "file_log.jsonl").read_text().splitlines()] == [
        "write", "edit"]

    out = tmp_path / "pkg"
    summary = export_run(session.ws.root, out, tmp_path / "no_cache.sqlite")
    assert summary["cells"] == 9 and summary["artifacts"] == 7 and summary["file_writes"] == 2 and summary["jobs"] == 1
    r = subprocess.run([sys.executable, str(out / "scripts" / "run_all.py"), "--db", str(SAMPLE_DB)],
                       capture_output=True, text=True, timeout=300, cwd=REPO)
    assert r.returncode == 0, r.stderr[-2000:]
    assert ("Artifacts recomputed and identical: 6; identical up to row order: 0 []; recomputed and different: 0 []; "
            "taken from the original run: 1 ['J4']; not recreated: 0 []") in r.stdout, r.stdout[-2000:]
    assert r.stdout.count("differs from the original run") == 1


def test_job_ids_stay_unique_and_stopped_jobs_are_recorded(session):
    (session.ws.root / "jobs" / "job3").mkdir(parents=True)  # a job folder from an earlier turn
    job = session.jobs.start("analyst", "slow", "import time\ntime.sleep(60)")
    assert job.id == "job4"
    session.jobs.shutdown()
    rec = json.loads((session.ws.root / "kernel_log.jsonl").read_text().splitlines()[-1])
    assert rec["job"] == "job4" and rec["stopped"] is True and rec["ok"] is False


def test_run_record_summarizes_turns_from_the_event_log(tmp_path):
    ev = [{"ts": 1000.0, "agent": "user", "kind": "message", "payload": {"text": "go"}},
          {"ts": 1001.0, "agent": "analyst", "kind": "cost", "payload": {"model": "m", "usd": 0.25}},
          {"ts": 1002.0, "agent": "critic", "kind": "gate", "payload": {"artifact": "P1", "verdict": "pass"}},
          {"ts": 1003.0, "agent": "system", "kind": "done", "payload": {"seconds": 120}},
          {"ts": 2000.0, "agent": "user", "kind": "message", "payload": {"text": "write"}},
          {"ts": 2001.0, "agent": "writer", "kind": "cost", "payload": {"model": "m", "usd": 0.5}},
          {"ts": 2002.0, "agent": "critic", "kind": "gate", "payload": {"artifact": "report", "verdict": "pass"}}]
    (tmp_path / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in ev))
    (tmp_path / "history" / "turn1").mkdir(parents=True)
    (tmp_path / "history" / "turn1" / "external_usage.json").write_text(json.dumps({"requests": 1234, "usd": 0.12}))
    text = rep.run_record(tmp_path)
    assert "| 1 | 1970-01-01 00:16 | 2 min | 1 | $0.25 | 1,234 | $0.12 |" in text
    assert "| 0 | 1, 1 passed | 0 |" in text and "| 0 | 0 | 1: pass |" in text
    assert "| writer | $0.00 | $0.50 | $0.50 |" in text and "| all | $0.25 | $0.50 | $0.75 |" in text


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
