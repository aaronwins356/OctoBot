from __future__ import annotations

import json
from pathlib import Path

from octobot.core.orchestrator import Orchestrator
from octobot.memory.utils import proposals_root, repo_root


def test_orchestrator_generates_proposal(tmp_path: Path) -> None:
    workspace = proposals_root() / "_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "coverage.json").write_text(json.dumps({"coverage": 0.95}), encoding="utf-8")

    orchestrator = Orchestrator()
    lifecycle = orchestrator.draft_proposal("Stability Enhancements")

    assert lifecycle.proposal.path.exists()
    metadata_path = lifecycle.proposal.path / "proposal.yaml"
    assert metadata_path.exists()
    data = metadata_path.read_text(encoding="utf-8")
    assert "awaiting_approval" in data
    assert lifecycle.validation is not None and lifecycle.validation.compliant

    ledger_path = repo_root() / "memory" / "ledger.json"
    assert ledger_path.exists()
    entries = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    proposal_entries = [
        entry for entry in entries if entry["proposal_id"] == lifecycle.proposal.proposal_id
    ]
    assert any(entry["status"] == "validated" for entry in proposal_entries)
