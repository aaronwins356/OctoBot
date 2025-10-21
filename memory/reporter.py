"""Aggregated metrics for OctoBot."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from memory.history_logger import HistoryLogger, MetricRecord, MetricStore


@dataclass
class AnalyzerSummary:
    files_scanned: int
    functions_flagged: int
    unused_imports: int
    missing_docstrings: int


class Reporter:
    def __init__(self, metric_store: MetricStore | None = None, logger: HistoryLogger | None = None) -> None:
        self.metric_store = metric_store or MetricStore()
        self.logger = logger or HistoryLogger()

    def record_analyzer_summary(self, summary: AnalyzerSummary) -> None:
        self.metric_store.log_metric("files_scanned", summary.files_scanned)
        self.metric_store.log_metric("functions_flagged", summary.functions_flagged)
        self.metric_store.log_metric("unused_imports", summary.unused_imports)
        self.metric_store.log_metric("missing_docstrings", summary.missing_docstrings)
        self.logger.log_event(
            "Analyzer summary recorded: "
            + ", ".join(
                f"{field}={getattr(summary, field)}"
                for field in ("files_scanned", "functions_flagged", "unused_imports", "missing_docstrings")
            )
        )

    def record_evaluator_scores(self, scores: Dict[str, float]) -> None:
        for key, value in scores.items():
            self.metric_store.log_metric(f"score_{key}", value)
        self.logger.log_event("Evaluator scores recorded: " + ", ".join(f"{k}={v}" for k, v in scores.items()))

    def latest_metrics(self) -> Dict[str, List[MetricRecord]]:
        keys = [
            "files_scanned",
            "functions_flagged",
            "unused_imports",
            "missing_docstrings",
            "score_complexity",
            "score_tests",
            "score_docs",
            "score_risk",
        ]
        return {key: self.metric_store.fetch_metrics(key) for key in keys}
