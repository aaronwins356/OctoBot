"""Law and ethics validation for OctoBot agents."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from utils_yaml import safe_load


@dataclass
class LawBook:
    rules: List[str]
    principles: List[str]


class LawViolation(Exception):
    """Raised when an operation violates a constitutional rule."""


class LawValidator:
    """Loads constitutional rules and enforces them against agent actions."""

    def __init__(self, constitution_path: Path | None = None, ethics_path: Path | None = None) -> None:
        base = Path(__file__).resolve().parent
        self.constitution_path = constitution_path or base / "constitution.yaml"
        self.ethics_path = ethics_path or base / "ethics.yaml"
        self._law_book: LawBook | None = None

    @property
    def law_book(self) -> LawBook:
        if self._law_book is None:
            with self.constitution_path.open("r", encoding="utf-8") as fh:
                constitution = safe_load(fh.read()) or {}
            with self.ethics_path.open("r", encoding="utf-8") as fh:
                ethics = safe_load(fh.read()) or {}
            self._law_book = LawBook(
                rules=list(constitution.get("rules", [])),
                principles=list(ethics.get("principles", [])),
            )
        return self._law_book

    def ensure(self, conditions: Iterable[str]) -> None:
        """Check conditions against the law book.

        Parameters
        ----------
        conditions:
            An iterable of textual statements that describe facts about the
            current operation. If any statement contradicts a rule the
            validator raises :class:`LawViolation`.
        """

        contradictions: list[str] = []
        facts = set(condition.lower() for condition in conditions)
        for rule in self.law_book.rules:
            lowered = rule.lower()
            if "without human approval" in lowered and "human approval" not in facts:
                contradictions.append(rule)
            if "no network requests" in lowered and "network request" in facts:
                contradictions.append(rule)
            if "log a rationale" in lowered and "rationale logged" not in facts:
                contradictions.append(rule)
        if contradictions:
            raise LawViolation(
                "Operation violates constitutional rule(s): " + ", ".join(contradictions)
            )

    def describe(self) -> str:
        book = self.law_book
        return "Rules: " + ", ".join(book.rules) + " | Principles: " + ", ".join(book.principles)


DEFAULT_VALIDATOR = LawValidator()
