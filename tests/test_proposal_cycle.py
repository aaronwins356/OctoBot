from __future__ import annotations

import json
from pathlib import Path

from government.orchestrator import Orchestrator
from memory.utils import proposals_root


def test_orchestrator_generates_proposal(tmp_path: Path) -> None:
    workspace = proposals_root() / "_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "coverage.json").write_text(json.dumps({"coverage": 0.95}), encoding="utf-8")

    orchestrator = Orchestrator()
    result = orchestrator.run_cycle("Stability Enhancements")

    assert result.proposal.path.exists()
    metadata_path = result.proposal.path / "proposal.yaml"
    assert metadata_path.exists()
    data = metadata_path.read_text(encoding="utf-8")
    assert "awaiting_approval" in data
    assert len(result.transitions) == 4
