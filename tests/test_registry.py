"""Tests for agent discovery registry."""
from __future__ import annotations

from pathlib import Path

from government.registry import discover_agents


def test_registry_discovers_writer_agent() -> None:
    agents = discover_agents(Path("entrepreneurs"))
    names = {agent.__name__ for agent in agents}
    assert "WriterAgent" in names
    assert "SimAgent" in names
