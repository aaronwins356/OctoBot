from __future__ import annotations

import pytest

from octobot.core.orchestrator import Orchestrator


def test_full_cycle_proposal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCTOBOT_DRY_RUN", "1")
    orchestrator = Orchestrator()
    lifecycle = orchestrator.draft_proposal("End-to-End Simulation")
    assert lifecycle.validation is not None and lifecycle.validation.compliant
    commit = orchestrator.approve_proposal(lifecycle.proposal.proposal_id, "tester")
    assert commit == "dry-run"
