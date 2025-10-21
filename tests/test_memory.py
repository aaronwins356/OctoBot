"""Tests for the memory recall subsystem."""
from pathlib import Path

from memory.recall import MemoryRecall


def test_memory_store_and_recall(tmp_path: Path) -> None:
    database_path = tmp_path / "brain.db"
    memory = MemoryRecall(database_path=str(database_path), embedding_dim=32)
    memory.store("summarize report", "Created a concise summary of the report")
    recalled = memory.recall("report summary")
    assert recalled is not None
    assert "summary" in recalled
