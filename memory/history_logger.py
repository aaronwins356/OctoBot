"""SQLite-backed logging for OctoBot."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple

DATABASE_PATH = Path(__file__).resolve().parent / "memory.db"


def _ensure_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS approvals (
            proposal_id TEXT PRIMARY KEY,
            approved_by TEXT NOT NULL,
            approved_at TEXT NOT NULL
        )
        """
    )
    connection.commit()


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        _ensure_tables(connection)
        yield connection
    finally:
        connection.close()


class HistoryLogger:
    """Persist history events and approvals for auditing."""

    def log_event(self, event: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        with _connect() as conn:
            conn.execute("INSERT INTO history(event, created_at) VALUES (?, ?)", (event, timestamp))
            conn.commit()

    def list_events(self, limit: int = 100) -> List[Tuple[str, str]]:
        with _connect() as conn:
            cursor = conn.execute(
                "SELECT event, created_at FROM history ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return list(cursor.fetchall())

    def approve(self, proposal_id: str, approved_by: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        with _connect() as conn:
            conn.execute(
                "REPLACE INTO approvals(proposal_id, approved_by, approved_at) VALUES (?, ?, ?)",
                (proposal_id, approved_by, timestamp),
            )
            conn.commit()
        self.log_event(f"Proposal {proposal_id} approved by {approved_by}")

    def is_approved(self, proposal_id: str) -> bool:
        with _connect() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM approvals WHERE proposal_id = ?",
                (proposal_id,),
            )
            return cursor.fetchone() is not None

    def list_approvals(self) -> List[Tuple[str, str, str]]:
        with _connect() as conn:
            cursor = conn.execute(
                "SELECT proposal_id, approved_by, approved_at FROM approvals ORDER BY approved_at DESC"
            )
            return list(cursor.fetchall())


@dataclass
class MetricRecord:
    key: str
    value: float
    captured_at: str


class MetricStore:
    def log_metric(self, key: str, value: float) -> None:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    key TEXT NOT NULL,
                    value REAL NOT NULL,
                    captured_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT INTO metrics(key, value, captured_at) VALUES (?, ?, ?)",
                (key, value, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def fetch_metrics(self, key: str, limit: int = 20) -> List[MetricRecord]:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    key TEXT NOT NULL,
                    value REAL NOT NULL,
                    captured_at TEXT NOT NULL
                )
                """
            )
            cursor = conn.execute(
                "SELECT key, value, captured_at FROM metrics WHERE key = ? ORDER BY captured_at DESC LIMIT ?",
                (key, limit),
            )
            return [MetricRecord(*row) for row in cursor.fetchall()]
