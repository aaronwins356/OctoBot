from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from octobot.core.proposal_manager import ProposalManager
from octobot.laws.validator import (
    RuleViolationError,
    enforce,
    guard,
    register_agent,
    validate_proposal,
)
from octobot.memory.utils import proposals_root


@given(
    st.text(min_size=1, max_size=12, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_filesystem_write_allows_proposals(filename: str) -> None:
    target = proposals_root() / filename
    enforce("filesystem_write", str(target))


def test_filesystem_write_blocks_root(tmp_path: Path) -> None:
    with pytest.raises(RuleViolationError):
        enforce("filesystem_write", str(Path.cwd() / "forbidden.txt"))


def test_code_merge_requires_approval() -> None:
    with pytest.raises(RuleViolationError):
        enforce("code_merge", "denied")
    enforce("code_merge", "approved")


def test_validate_proposal_checks_quality() -> None:
    manager = ProposalManager()
    lifecycle = manager.generate("Law Compliance", {"coverage": 0.95, "findings": []})
    report = validate_proposal(lifecycle)
    assert report.compliant


def test_validate_proposal_flags_low_coverage(tmp_path: Path) -> None:
    manager = ProposalManager()
    proposal = manager.generate("Low Coverage", {"coverage": 0.2, "findings": []})
    report = validate_proposal(proposal)
    assert not report.compliant
    assert any("coverage" in issue for issue in report.issues)


def test_guard_enforces_registration() -> None:
    @guard("temp-agent")
    def _action() -> bool:
        return True

    with pytest.raises(RuleViolationError):
        _action()

    register_agent("temp-agent")
    assert _action() is True
