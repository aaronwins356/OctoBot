"""SQLite database helpers for memory and ledger persistence."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)

_DB_PATH = Path(SETTINGS.runtime.db_path)
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    """Initialise the SQLite schema if missing."""

    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    LOGGER.debug("Memory database initialised at %s", _DB_PATH)


def insert_event(agent: str, payload: Dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO memory_events(agent, payload) VALUES (?, ?)",
            (agent, json.dumps(payload)),
        )
        conn.commit()


def fetch_recent(limit: int) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT agent, payload, created_at FROM memory_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    results: List[Dict[str, Any]] = []
    for row in rows:
        payload = json.loads(row["payload"])
        payload["agent"] = row["agent"]
        payload["created_at"] = row["created_at"]
        results.append(payload)
    return results


__all__ = ["init", "insert_event", "fetch_recent"]
