"""SQLite database utilities for The Brain memory layer."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Tuple


class DatabaseManager:
    """Manage the SQLite database storing task logs and insights."""

    def __init__(self, database_path: str = "data/brain.db") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT NOT NULL,
                    insight TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def insert_task(self, task: str, response: str) -> None:
        """Persist a completed task and its response."""

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO tasks (task, response) VALUES (?, ?)",
                (task, response),
            )
            connection.commit()

    def fetch_recent_tasks(self, limit: int = 5) -> Iterable[Tuple[str, str]]:
        """Return the most recent tasks and responses."""

        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                "SELECT task, response FROM tasks ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            yield from cursor.fetchall()

    def insert_insight(self, goal: str, insight: str) -> None:
        """Persist a reflective insight."""

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO insights (goal, insight) VALUES (?, ?)",
                (goal, insight),
            )
            connection.commit()

    def fetch_recent_insights(self, limit: int = 5) -> Iterable[Tuple[str, str]]:
        """Retrieve recent insights for reference."""

        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                "SELECT goal, insight FROM insights ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            yield from cursor.fetchall()
