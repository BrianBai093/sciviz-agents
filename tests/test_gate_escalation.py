"""The verification gate's retry -> escalate -> stop state machine (no browser, no LLM: source errors only)."""
import dataclasses

import pytest

import sciviz.harness.budget as budget_mod
import sciviz.session as session_mod
import sciviz.tools.viz_tools as viz_mod


@pytest.fixture()
def session(tmp_path, monkeypatch):
    s = dataclasses.replace(session_mod.settings, workspaces_dir=tmp_path, max_gate_revisions=2)
    for mod in (session_mod, budget_mod, viz_mod):
        monkeypatch.setattr(mod, "settings", s)
    sess = session_mod.Session("gate-test")
    yield sess
    sess.close()


def test_retry_then_escalate_then_stop(session):
    submit = viz_mod.viz_tools(session, "viz")[1]
    outputs = [submit.invoke({"slug": "missing", "acceptance_criteria": ""}) for _ in range(4)]
    assert outputs[0].startswith("REVISE (attempt 1 of 2)")
    assert outputs[1].startswith("REVISE (final attempt")      # 2nd failure reaches the limit -> escalate
    assert outputs[2].startswith("STOP")                        # escalated round failed too -> stop
    assert "viz" not in session.escalate_agents                 # escalation flag cleared at stop
    kinds = [e["payload"].get("escalation") for e in session.events.read_all() if e["kind"] == "plan"]
    assert any(k and "escalated" in k for k in kinds)
