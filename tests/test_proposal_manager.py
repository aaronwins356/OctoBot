from __future__ import annotations

from pathlib import Path


from government import proposal_manager
from government.proposal_manager import VentureProposal


def test_save_and_load_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(proposal_manager.SETTINGS.runtime, "proposal_dir", str(tmp_path))
    proposal = VentureProposal(
        proposal_id="demo",
        proposal_name="Demo Venture",
        author_agent="venture_agent",
        description="Example venture for testing.",
        expected_cost="$0",
        expected_revenue="$100",
        strategy="Test strategy",
        ethical_statement="Operate ethically.",
        files_created=["file.txt"],
        status="draft",
    )
    manifest = proposal_manager.save_proposal(proposal, base_path=tmp_path)
    loaded = proposal_manager.load_proposal(manifest)
    assert loaded.proposal_name == proposal.proposal_name
    assert loaded.files_created == ["file.txt"]


def test_filter_approved(tmp_path: Path) -> None:
    approved = VentureProposal(
        proposal_id="1",
        proposal_name="Approved",
        author_agent="venture_agent",
        description="",
        expected_cost="$0",
        expected_revenue="$0",
        strategy="",
        ethical_statement="",
        status="approved",
    )
    pending = VentureProposal(
        proposal_id="2",
        proposal_name="Pending",
        author_agent="venture_agent",
        description="",
        expected_cost="$0",
        expected_revenue="$0",
        strategy="",
        ethical_statement="",
        status="draft",
    )
    filtered = proposal_manager.filter_approved([approved, pending])
    assert filtered == [approved]
