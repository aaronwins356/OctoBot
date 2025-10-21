"""Tests for orchestrator dry-run execution."""
from __future__ import annotations

import memory
from government import orchestrator


def test_run_all_agents_dry_run(monkeypatch):
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(memory, "store_event", lambda agent, event: events.append((agent, event)))

    def fail_run(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("Subprocess should not run during dry run")

    monkeypatch.setattr(orchestrator, "run_agent_subprocess", fail_run)

    orchestrator.run_all_agents(dry_run=True)
    assert events
    for _, event in events:
        assert event["status"] == "validated"
