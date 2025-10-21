"""Analytics and reporting utilities for OctoBot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .history_logger import MemoryStore, ProposalRecord
from .logger import log_event


@dataclass
class AnalyzerSummary:
    files_scanned: int
    complexity_issues: int
    todos: int
    missing_docstrings: int
    coverage: float


class Reporter:
    """Capture metrics and provide dashboard-ready aggregates."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def record_analyzer_summary(self, summary: AnalyzerSummary) -> None:
        self.store.log_metric("files_scanned", float(summary.files_scanned))
        self.store.log_metric("complexity_issues", float(summary.complexity_issues))
        self.store.log_metric("todos", float(summary.todos))
        self.store.log_metric("missing_docstrings", float(summary.missing_docstrings))
        self.store.log_metric("coverage", summary.coverage)
        log_event(
            "reporter",
            "analyzer_summary",
            "recorded",
            {
                "files_scanned": summary.files_scanned,
                "complexity_issues": summary.complexity_issues,
                "todos": summary.todos,
                "missing_docstrings": summary.missing_docstrings,
                "coverage": summary.coverage,
            },
        )

    def latest_metrics(self) -> Dict[str, List[Dict[str, str]]]:
        keys = ["files_scanned", "complexity_issues", "todos", "missing_docstrings", "coverage"]
        return {key: self.store.fetch_metrics(key) for key in keys}

    def generate_weekly_summary(self) -> Dict[str, Dict[str, int]]:
        proposal_summary = self.store.proposals_summary_last_week()
        return {"proposals": proposal_summary}

    def proposals(self) -> List[ProposalRecord]:
        return self.store.list_proposals()
