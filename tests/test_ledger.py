"""The spend ledger survives concurrent writers from several processes (regression test for D41)."""
import json
import multiprocessing as mp

from sciviz.harness.budget import SpendLedger


def _writer(path, n):
    led = SpendLedger(path)
    for _ in range(n):
        led.record("s", "a", "gpt-6.2-sol", {"input_tokens": 1000, "output_tokens": 100})


def test_concurrent_processes(tmp_path):
    path = tmp_path / "_ledger.json"
    SpendLedger(path)
    procs = [mp.get_context("spawn").Process(target=_writer, args=(path, 25)) for _ in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    d = json.loads(path.read_text())
    assert d["calls"] == 100
    assert abs(d["total_usd"] - 100 * (1000 * 2 + 100 * 10) / 1e6) < 1e-6


def test_rebuild_from_events_when_damaged(tmp_path):
    (tmp_path / "s1").mkdir()
    ev = {"ts": 0, "session": "s1", "agent": "viz", "kind": "cost",
          "payload": {"model": "gpt-6.2-sol", "usd": 0.25, "input_tokens": 1, "output_tokens": 1}}
    (tmp_path / "s1" / "events.jsonl").write_text(json.dumps(ev) + "\n")
    path = tmp_path / "_ledger.json"
    path.write_text("{ damaged")
    assert SpendLedger(path).total == 0.25
