from __future__ import annotations

from pathlib import Path

from government.proposal_manager import ProposalManager


def test_proposal_generation_creates_yaml(tmp_path: Path) -> None:
    report = {
        "findings": [
            {
                "file_path": "module.py",
                "issue_type": "complexity",
                "detail": "Complex function",
            }
        ],
        "unused_imports": 1,
        "missing_docstrings": 2,
        "files_scanned": 1,
    }
    manager = ProposalManager(repo_root=tmp_path)
    proposals = manager.generate(report)
    assert proposals
    proposal = proposals[0]
    assert (proposal.path / "proposal.yaml").exists()
