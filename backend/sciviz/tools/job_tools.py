"""Background-job tools (report mode): start a long script, check it, wait for it."""
from __future__ import annotations

from langchain_core.tools import tool

from ..session import Session
from .data_tools import _emit_call, _emit_result


def job_tools(s: Session, agent: str):
    @tool
    def start_job(name: str, code: str) -> str:
        """Run a long Python script as a background job: a separate process with the same helpers as
        `run_python` (sql, load, save_table, save_json, record_finding and, in report mode, openalex,
        openalex_many, openalex_usage). It does NOT share your kernel's variables: load inputs from artifacts,
        save results as artifacts, and print progress lines (job_status shows the log). Use it for work longer
        than about two minutes, such as bulk external collection. Write it so that a rerun is cheap and safe
        (cached API responses are free). Returns a job id."""
        _emit_call(s, agent, "start_job", {"name": name, "code": code})
        job = s.jobs.start(agent, name, code)
        text = f"Started {job.id} '{name}'. Check it with job_status('{job.id}') or wait_job('{job.id}')."
        _emit_result(s, agent, "start_job", True, text)
        return text

    @tool
    def job_status(job_id: str) -> str:
        """State of a background job (running / finished / failed), elapsed time, the artifacts it created
        and the end of its log."""
        try:
            return s.jobs.describe(s.jobs.poll(job_id))
        except KeyError as e:
            return str(e)

    @tool
    def wait_job(job_id: str, max_wait_s: int = 600) -> str:
        """Wait until a background job ends or `max_wait_s` seconds pass (at most 900), then return its status."""
        _emit_call(s, agent, "wait_job", {"job_id": job_id, "max_wait_s": max_wait_s})
        try:
            job = s.jobs.wait(job_id, max(5, min(int(max_wait_s), 900)))
            text, ok = s.jobs.describe(job), job.ended is None or job.returncode == 0
        except KeyError as e:
            text, ok = str(e), False
        _emit_result(s, agent, "wait_job", ok, text)
        return text

    return [start_job, job_status, wait_job]
