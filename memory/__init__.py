"""High-level memory APIs for storing and retrieving agent events."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any, Dict, List

from utils.logger import get_logger
from utils.settings import SETTINGS

from . import db

LOGGER = get_logger(__name__)

db.init()


def store_event(agent: str, event: Dict[str, Any]) -> None:
    """Persist an event in SQLite."""

    LOGGER.info("Storing memory event for %s", agent)
    db.insert_event(agent, event)


def query_recent(limit: int = 5) -> List[Dict[str, Any]]:
    """Return the most recent memory events."""

    return db.fetch_recent(limit)


def summarize_recent(limit: int = 5) -> str:
    """Produce a concise summary of recent events."""

    events = query_recent(limit)
    if not events:
        return "No recent events recorded."
    lines = []
    for item in events:
        summary = textwrap.shorten(str(item), width=120)
        lines.append(f"- {item['created_at']}: {summary}")
    return "\n".join(lines)


def write_reflection(content: str) -> Path:
    """Write reflection notes to the reflections directory."""

    reflections_dir = Path(SETTINGS.runtime.reflections_dir)
    reflections_dir.mkdir(parents=True, exist_ok=True)
    filename = reflections_dir / "reflection.txt"
    filename.write_text(content, encoding="utf-8")
    LOGGER.info("Reflection written to %s", filename)
    return filename


__all__ = ["store_event", "query_recent", "summarize_recent", "write_reflection"]
