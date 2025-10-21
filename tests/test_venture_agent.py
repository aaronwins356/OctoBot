from __future__ import annotations

from pathlib import Path

import yaml

from entrepreneurs.venture_agent import VentureAgent
from government import proposal_manager


def test_venture_agent_creates_manifest(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(proposal_manager.SETTINGS.runtime, "proposal_dir", str(tmp_path))
    sandbox = tmp_path / "sandbox"
    agent = VentureAgent("venture_agent", str(sandbox))
    agent.setup()
    result = agent.run({})
    manifest = Path(result["proposal_manifest"])
    assert manifest.exists()
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert data["proposal_name"] == "Grounded Affiliate Blog"
    assert data["status"] == "draft"
