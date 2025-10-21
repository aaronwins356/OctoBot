from __future__ import annotations

from pathlib import Path

import yaml

from government import proposal_manager
from government.presenter import build_portfolio


def test_build_portfolio_creates_homepage(tmp_path: Path, monkeypatch) -> None:
    proposals_dir = tmp_path / "scriptSuggestions"
    proposal_folder = proposals_dir / "demo"
    proposal_folder.mkdir(parents=True)
    manifest = proposal_folder / "proposal.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "proposal_id": "demo",
                "proposal_name": "Demo Venture",
                "author_agent": "venture_agent",
                "description": "Test venture",
                "expected_cost": "$0",
                "expected_revenue": "$10",
                "strategy": "Test",
                "ethical_statement": "Ethical",
                "files_created": [],
                "status": "approved",
                "require_human_approval": True,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(proposal_manager.SETTINGS.runtime, "proposal_dir", str(proposals_dir))
    output_dir = tmp_path / "public"
    files = build_portfolio(output_dir=output_dir, template_dir=Path("website/templates"))
    index = output_dir / "index.html"
    assert index.exists()
    assert "Demo Venture" in index.read_text(encoding="utf-8")
    assert files
