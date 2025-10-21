"""Tests for sandbox path isolation."""
from __future__ import annotations

from pathlib import Path

import pytest

from government.sandbox import SandboxPaths
from laws.enforcement import LawViolation, verify_agent_permissions
from utils.settings import SETTINGS


def test_sandbox_creation_respects_root() -> None:
    sandbox = SandboxPaths.create("test_agent")
    assert sandbox.root.is_dir()
    assert sandbox.root.resolve().is_relative_to(Path(SETTINGS.runtime.sandbox_root).resolve())


def test_verify_agent_permissions_blocks_outside_paths() -> None:
    with pytest.raises(LawViolation):
        verify_agent_permissions(Path("README.md"))
