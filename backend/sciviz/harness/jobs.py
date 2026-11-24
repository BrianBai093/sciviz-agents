"""Background jobs (Project 2, PLAN_P2 §3.3): long scripts that outlive one tool call.

A job is agent-written Python run in its own process, with the same helpers and environment as the agent's
kernel (no secrets; external API only through the harness proxy). It reads inputs from artifacts and saves its
results as artifacts. Progress goes to jobs/<id>/log.txt. When a job ends, the artifacts it created are tagged
with its code and the cell is added to the kernel log, so script export can replay it.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..tools.python_exec import PRELUDE, clean_env


@dataclass
class Job:
    id: str
    name: str
    agent: str
    code: str
    dir: Path
    started: float
    proc: subprocess.Popen
    ended: float | None = None
    returncode: int | None = None
    created: list[str] = field(default_factory=list)


class JobManager:
    def __init__(self, session):
        self.s = session
        self.root = session.ws.root / "jobs"
        self.jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def start(self, agent: str, name: str, code: str) -> Job:
        with self._lock:
            jid = f"job{len(self.jobs) + 1}"
            d = self.root / jid
            d.mkdir(parents=True, exist_ok=True)
            (d / "script.py").write_text(code, encoding="utf8")
            (d / "run.py").write_text(PRELUDE + "\n\n# ---- job script ----\n" + code, encoding="utf8")
            env = clean_env({"SCIVIZ_WORKSPACE": str(self.s.ws.root), "SCIVIZ_DB": str(self.s.kernels.db_path),
                             "SCIVIZ_AGENT": agent, "PYTHONUNBUFFERED": "1", **self.s.kernels.extra_env})
            log = open(d / "log.txt", "w", encoding="utf8")  # noqa: SIM115 (owned by the child process)
            proc = subprocess.Popen([sys.executable, str(d / "run.py")], cwd=str(self.s.ws.root), env=env,
                                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            job = Job(jid, name, agent, code, d, time.time(), proc)
            self.jobs[jid] = job
        self._write_meta(job)
        self.s.events.emit(agent, "job", action="start", job=jid, name=name)
        return job

    def poll(self, jid: str) -> Job:
        job = self.jobs.get(jid)
        if job is None:
            raise KeyError(f"No job {jid!r}; jobs: {', '.join(self.jobs) or '(none)'}")
        if job.ended is None and job.proc.poll() is not None:
            self._finish(job)
        return job

    def wait(self, jid: str, max_wait_s: float) -> Job:
        deadline = time.time() + max_wait_s
        job = self.poll(jid)
        while job.ended is None and time.time() < deadline:
            time.sleep(2)
            job = self.poll(jid)
        return job

    def describe(self, job: Job, tail: int = 30) -> str:
        state = "running" if job.ended is None else ("finished" if job.returncode == 0 else
                                                       f"failed (exit code {job.returncode})")
        elapsed = (job.ended or time.time()) - job.started
        lines = (job.dir / "log.txt").read_text(encoding="utf8", errors="replace").splitlines()
        text = f"{job.id} '{job.name}': {state} after {elapsed:.0f}s"
        if job.ended is not None:
            text += f"; artifacts created: {', '.join(job.created) or 'none'}"
        text += f"\nlog ({len(lines)} lines, last {min(tail, len(lines))}):\n" + "\n".join(lines[-tail:])
        if self.s.openalex is not None:
            text += "\n" + self.s.openalex.usage_text()
        return text

    def shutdown(self) -> None:
        for job in self.jobs.values():
            if job.ended is None and job.proc.poll() is None:
                try:
                    os.killpg(job.proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

    def _finish(self, job: Job) -> None:
        from ..tools.data_tools import log_cell
        job.ended, job.returncode = time.time(), job.proc.returncode
        for m in self.s.ws.list():
            if (m["kind"] not in ("viz", "figure") and m.get("producer") == job.agent and not m.get("code")
                    and job.started <= m.get("created_at", 0) <= job.ended + 1):
                self.s.ws.update_meta(m["id"], code=job.code, job=job.id)
                self.s.events.emit(job.agent, "artifact", id=m["id"], artifact_kind=m["kind"], title=m["title"])
                job.created.append(m["id"])
        log_cell(self.s, job.agent, job.code, job.returncode == 0, job.created, job.started, job=job.id)
        self._write_meta(job)
        self.s.events.emit(job.agent, "job", action="end", job=job.id, returncode=job.returncode,
                           seconds=round(job.ended - job.started, 1), created=job.created)

    def _write_meta(self, job: Job) -> None:
        (job.dir / "job.json").write_text(json.dumps({
            "id": job.id, "name": job.name, "agent": job.agent, "started": job.started, "ended": job.ended,
            "returncode": job.returncode, "created": job.created}, indent=2))
