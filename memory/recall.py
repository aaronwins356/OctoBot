"""Semantic recall functionality backed by deterministic embeddings."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from memory.database import DatabaseManager
from memory.embeddings import cosine_similarity, embed_text


@dataclass
class MemoryItem:
    """A stored memory containing task text and response."""

    task: str
    response: str
    embedding: List[float]


@dataclass
class MemoryRecall:
    """Provide recall and storage for past tasks."""

    database_path: str = "data/brain.db"
    embedding_dim: int = 128
    _items: List[MemoryItem] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.database = DatabaseManager(self.database_path)
        self._load_from_database()

    def _load_from_database(self) -> None:
        for task, response in self.database.fetch_recent_tasks(limit=100):
            self._items.append(
                MemoryItem(
                    task=task,
                    response=response,
                    embedding=embed_text(task, self.embedding_dim),
                )
            )

    def store(self, task: str, response: str) -> None:
        """Store a completed task and persist it to the database."""

        embedding = embed_text(task, self.embedding_dim)
        self._items.append(MemoryItem(task=task, response=response, embedding=embedding))
        self.database.insert_task(task, response)

    def recall(self, query: str) -> Optional[str]:
        """Return the most similar memory for the provided query."""

        if not self._items:
            return None
        query_embedding = embed_text(query, self.embedding_dim)
        scored: List[Tuple[float, MemoryItem]] = []
        for item in self._items:
            score = cosine_similarity(query_embedding, item.embedding)
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        best_score, best_item = scored[0]
        if best_score < 0.2:
            return None
        return best_item.response

    def store_insight(self, goal: str, insight: str) -> None:
        """Persist a reflective insight and keep a local copy."""

        self.database.insert_insight(goal, insight)

    def recent_tasks(self) -> List[MemoryItem]:
        """Return recent tasks in memory order."""

        return list(self._items[-10:])
