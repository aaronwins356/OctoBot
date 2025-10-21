from pathlib import Path

from octobot.core.proposals import ProposalManager


def test_proposal_manager_persists(tmp_path):
    path = tmp_path / "proposals.json"
    manager = ProposalManager(store_path=path)
    proposal = manager.create("Test Proposal", {"coverage": 0.91})
    assert proposal.state == "pending"
    assert proposal.metadata["coverage"] == 0.91

    reloaded = ProposalManager(store_path=path)
    assert reloaded.exists(proposal.id)
    stored = reloaded.get(proposal.id)
    assert stored.metadata["coverage"] == 0.91


def test_mark_approved_and_rejected(tmp_path):
    path = tmp_path / "proposals.json"
    manager = ProposalManager(store_path=path)
    proposal = manager.create("Another", {})

    manager.mark_approved(proposal.id, approver="tester", token="abc")
    assert manager.get(proposal.id).state == "approved"
    assert manager.get(proposal.id).metadata["approved_by"] == "tester"

    manager.mark_rejected(proposal.id, reason="no")
    rejected = manager.get(proposal.id)
    assert rejected.state == "rejected"
    assert rejected.metadata["reason"] == "no"
