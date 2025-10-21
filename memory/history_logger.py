"""Database-backed storage for OctoBot state."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .logger import log_event
from .utils import ensure_directory, repo_root, timestamp

_DB_PATH = repo_root() / "memory" / "memory.db"
ensure_directory(_DB_PATH.parent)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                path TEXT NOT NULL,
                approval_date TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value REAL NOT NULL,
                captured_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


_ENSURED = False


def _initialise() -> None:
    global _ENSURED
    if not _ENSURED:
        _ensure_schema()
        _ENSURED = True


@dataclass
class HistoryRecord:
    time: str
    agent: str
    action: str
    details: str


@dataclass
class ProposalRecord:
    proposal_id: str
    topic: str
    status: str
    created_at: str
    path: str
    approval_date: Optional[str]


class MemoryStore:
    """High level accessors for the SQLite storage."""

    def __init__(self) -> None:
        _initialise()

    def log_history(self, agent: str, action: str, details: str) -> None:
        log_event(agent, action, "recorded", details)
        with _connect() as conn:
            conn.execute(
                "INSERT INTO history(time, agent, action, details) VALUES (?, ?, ?, ?)",
                (timestamp(), agent, action, details),
            )
            conn.commit()

    def list_history(self, limit: int = 100) -> List[HistoryRecord]:
        with _connect() as conn:
            cursor = conn.execute(
                "SELECT time, agent, action, details FROM history ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [HistoryRecord(**dict(row)) for row in cursor.fetchall()]

    def upsert_proposal(self, proposal: ProposalRecord) -> None:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO proposals(id, topic, status, created_at, path, approval_date)
                VALUES(:proposal_id, :topic, :status, :created_at, :path, :approval_date)
                ON CONFLICT(id) DO UPDATE SET
                    topic=excluded.topic,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    path=excluded.path,
                    approval_date=excluded.approval_date
                """,
                proposal.__dict__,
            )
            conn.commit()

    def update_proposal_status(self, proposal_id: str, status: str, approval_date: Optional[str] = None) -> None:
        with _connect() as conn:
            conn.execute(
                "UPDATE proposals SET status = ?, approval_date = ? WHERE id = ?",
                (status, approval_date, proposal_id),
            )
            conn.commit()

    def fetch_proposal(self, proposal_id: str) -> Optional[ProposalRecord]:
        with _connect() as conn:
            cursor = conn.execute(
                "SELECT id as proposal_id, topic, status, created_at, path, approval_date FROM proposals WHERE id = ?",
                (proposal_id,),
            )
            row = cursor.fetchone()
            return ProposalRecord(**dict(row)) if row else None

    def list_proposals(self) -> List[ProposalRecord]:
        with _connect() as conn:
            cursor = conn.execute(
                "SELECT id as proposal_id, topic, status, created_at, path, approval_date FROM proposals ORDER BY created_at DESC",
            )
            return [ProposalRecord(**dict(row)) for row in cursor.fetchall()]

    def record_error(self, agent: str, message: str) -> None:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO errors(timestamp, agent, message) VALUES (?, ?, ?)",
                (timestamp(), agent, message),
            )
            conn.commit()

    def log_metric(self, key: str, value: float) -> None:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO metrics(key, value, captured_at) VALUES (?, ?, ?)",
                (key, value, timestamp()),
            )
            conn.commit()

    def fetch_metrics(self, key: str, limit: int = 20) -> List[Dict[str, str]]:
        with _connect() as conn:
            cursor = conn.execute(
                "SELECT key, value, captured_at FROM metrics WHERE key = ? ORDER BY captured_at DESC LIMIT ?",
                (key, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def proposals_summary_last_week(self) -> Dict[str, int]:
        since = (datetime.utcnow() - timedelta(days=7)).isoformat()
        with _connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM proposals WHERE created_at >= ?", (since,)).fetchone()[0]
            approved = conn.execute(
                "SELECT COUNT(*) FROM proposals WHERE approval_date IS NOT NULL AND approval_date >= ?",
                (since,),
            ).fetchone()[0]
            return {"created": total, "approved": approved}


class HistoryLogger:
    """Compatibility wrapper for previous API."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def log_event(self, message: str) -> None:
        self.store.log_history(agent="system", action="event", details=message)

    def list_events(self, limit: int = 100) -> List[str]:
        return [record.details for record in self.store.list_history(limit=limit)]

    def approve(self, proposal_id: str, approved_by: str) -> None:
        approval_time = timestamp()
        self.store.update_proposal_status(proposal_id, status="approved", approval_date=approval_time)
        self.store.log_history(agent="governance", action="approve", details=f"{approved_by}:{proposal_id}")

    def is_approved(self, proposal_id: str) -> bool:
        record = self.store.fetch_proposal(proposal_id)
        return bool(record and record.approval_date)

    def list_approvals(self) -> List[str]:
        return [record.proposal_id for record in self.store.list_proposals() if record.approval_date]
