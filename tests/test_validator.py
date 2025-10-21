from __future__ import annotations

from pathlib import Path

import pytest

from laws.validator import RuleViolationError, enforce
from memory.utils import proposals_root


def test_filesystem_write_allows_proposals(tmp_path: Path) -> None:
    target = proposals_root() / "_workspace" / "test.txt"
    enforce("filesystem_write", str(target))


def test_filesystem_write_blocks_root(tmp_path: Path) -> None:
    with pytest.raises(RuleViolationError):
        enforce("filesystem_write", str(Path.cwd() / "forbidden.txt"))


def test_code_merge_requires_approval() -> None:
    with pytest.raises(RuleViolationError):
        enforce("code_merge", "denied")
    enforce("code_merge", "approved")
