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


def test_reader_text_shows_figures_as_a_reader_sees_them():
    md = "## Results\n\nFigure P1 shows the trend [F1].\n\n{{figure:P1}}\n"
    text = rep.reader_text(md, ARTS)
    assert "Figure 1 shows the trend" in text and "[Figure 1. Fig. cap]" in text and "{{figure" not in text


def test_report_gate_needs_both_the_reviewer_and_the_reader(session, monkeypatch):
    from sciviz.agents import critic
    from sciviz.tools.report_tools import report_tools

    reader_calls = []

    def review_report(*a, **k):
        return critic.ReportVerdict(verdict="pass", support=5, coverage=5, honesty=5, clarity=5, summary="ok")

    def review_readability(text, **k):
        reader_calls.append(text)
        if len(reader_calls) == 1:
            return critic.ReadabilityVerdict(verdict="revise", readability=2, summary="hard to follow", issues=[
                critic.Issue(severity="major", problem='"the strict set" is never explained', fix="say which works")])
        return critic.ReadabilityVerdict(verdict="pass", readability=5, summary="clear")

    monkeypatch.setattr(critic, "review_report", review_report)
    monkeypatch.setattr(critic, "review_readability", review_readability)
    monkeypatch.setattr(rep, "render_pdf", lambda html_text, h, p: (h.write_text(html_text), p.write_bytes(b"%PDF")))
    write, remove, _draft, submit = report_tools(session, "writer")
    write.invoke({"position": 1, "name": "summary", "markdown": "## Summary\n\nThe answer [brief]."})
    write.invoke({"position": 2, "name": "old notes", "markdown": "## Notes\n\nKept by mistake [brief]."})
    assert remove.invoke({"name": "old notes"}) == "Removed 02_old-notes.md."
    first = submit.invoke({"title": "A report"})
    assert "needs revision (round 1 of 4)" in first and "(reader)" in first and "strict set" in first
    assert "Kept by mistake" not in reader_calls[0] and "The answer" in reader_calls[0]
    second = submit.invoke({"title": "A report"})
    assert "approved in round 2" in second
    reviews = [json.loads(x) for x in (session.ws.root / "report" / "reviews.jsonl").read_text().splitlines()]
    assert [r["verdict"] for r in reviews] == ["revise", "pass"] and reviews[0]["reader"]["verdict"] == "revise"
    assert json.loads((session.ws.root / "report" / "status.json").read_text())["scores"]["readability"] == 5


def test_a_new_turn_archives_the_released_report(tmp_path):
    from sciviz.cli import _archive_previous_turn
    root = tmp_path
    (root / "inputs").mkdir()
    (root / "report").mkdir()
    for name, text in [("lead_report.md", "lead"), ("inputs/run_constraints.md", "c"), ("external_usage.json", "{}"),
                       ("report/report.md", "# R"), ("report/status.json", "{}"), ("report/reviews.jsonl", "{}\n")]:
        (root / name).write_text(text)
    _archive_previous_turn(root)
    turn = root / "history" / "turn1"
    assert (turn / "lead_report.md").exists() and (turn / "report" / "report.md").read_text() == "# R"
    assert (root / "report" / "report.md").exists()  # still the current report until a new one passes the gate
    assert (turn / "report" / "reviews.jsonl").exists() and not (root / "report" / "reviews.jsonl").exists()


def test_exported_report_gets_the_harness_reproduction_section(tmp_path):
    from sciviz.harness.export import _reproduce_note
    ws, out = tmp_path / "ws", tmp_path / "pkg"
    ws.mkdir()
    out.mkdir()
    (ws / "kernel_log.jsonl").write_text('{"a": 1}\n{"a": 2}\n')
    (out / "REPRODUCE.md").write_text("x")
    note = _reproduce_note(ws, out)
    assert note.startswith("## How to reproduce this report") and "the 2 code steps" in note
    assert "/scripts/run_all.py" in note and "REPRODUCE.md" in note and "api_responses" not in note


def test_a_stopped_turn_is_archived_too(tmp_path):
    from sciviz.cli import _archive_previous_turn
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "run_constraints.md").write_text("stopped turn")  # no lead report: the turn was stopped
    _archive_previous_turn(tmp_path)
    assert (tmp_path / "history" / "turn1" / "run_constraints.md").read_text() == "stopped turn"
    _archive_previous_turn(tmp_path)  # nothing left to archive: no empty turn folder
    assert not (tmp_path / "history" / "turn2").exists()


def test_reviewer_evidence_puts_cited_artifacts_first(tmp_path):
    import pandas as pd
    arts = {}
    for i in range(1, 300):  # a long run: many artifacts the report does not cite
        arts[f"T{i}"] = {"id": f"T{i}", "kind": "table", "title": f"table {i}", "description": "x" * 400,
                         "summary": "y" * 900, "file": "data.parquet"}
    d = tmp_path / "artifacts" / "T299"
    d.mkdir(parents=True)
    pd.DataFrame({"group": ["a", "b"], "gap": [0.0812, 0.0885]}).to_parquet(d / "data.parquet")
    text = rep.evidence_text(arts, tmp_path, cited={"T299", "brief"}, limit=20000)
    assert text.startswith("T299 (table)") and "0.0812" in text  # the cited small table, with its rows
    assert "T5 (table) table 5\n" in text and "x" * 400 not in text.split("OTHER ARTIFACTS")[1]


def test_open_reader_points_stay_out_of_the_released_report(session, monkeypatch):
    from sciviz.agents import critic
    from sciviz.tools import report_tools as rt
    monkeypatch.setattr(rt, "REPORT_ROUNDS", 1)
    monkeypatch.setattr(critic, "review_report", lambda *a, **k: critic.ReportVerdict(
        verdict="pass", support=5, coverage=5, honesty=5, clarity=4, summary="ok"))
    monkeypatch.setattr(critic, "review_readability", lambda *a, **k: critic.ReadabilityVerdict(
        verdict="revise", readability=4, summary="one sentence is hard", issues=[
            critic.Issue(severity="major", problem="a long sentence", fix="split it")]))
    monkeypatch.setattr(rep, "render_pdf", lambda html_text, h, p: (h.write_text(html_text), p.write_bytes(b"%PDF")))
    write, _remove, _draft, submit = rt.report_tools(session, "writer")
    write.invoke({"position": 1, "name": "summary", "markdown": "## Summary\n\nThe answer [brief]."})
    assert "approved_with_issues in round 1" in submit.invoke({"title": "R"})
    root = session.ws.root / "report"
    assert "Open review issues" not in (root / "report.md").read_text()
    assert json.loads((root / "status.json").read_text())["open_reader_points"] == ["a long sentence"]
