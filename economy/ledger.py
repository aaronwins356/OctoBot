"""Simulated credit ledger for AI Republic."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict

from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)

_LEDGER_PATH = Path(SETTINGS.runtime.ledger_path)
_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_LEDGER_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger (
                agent TEXT PRIMARY KEY,
                credits INTEGER NOT NULL
            )
            """
        )
        conn.commit()
    LOGGER.debug("Ledger initialised at %s", _LEDGER_PATH)


def add_agent(agent: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO ledger(agent, credits) VALUES (?, ?)",
            (agent, SETTINGS.simulation.starting_credit),
        )
        conn.commit()


def add_credits(agent: str, amount: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE ledger SET credits = credits + ? WHERE agent = ?",
            (amount, agent),
        )
        conn.commit()
    LOGGER.info("Agent %s credited %s", agent, amount)


def get_balance(agent: str) -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT credits FROM ledger WHERE agent = ?",
            (agent,),
        ).fetchone()
    if row is None:
        return 0
    return int(row["credits"])


def snapshot() -> Dict[str, int]:
    with _connect() as conn:
        rows = conn.execute("SELECT agent, credits FROM ledger").fetchall()
    return {row["agent"]: int(row["credits"]) for row in rows}


init()

__all__ = ["add_agent", "add_credits", "get_balance", "snapshot"]
