"""Reflection engine for summarising performance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from orchestrator.evaluator import EvaluationResult


@dataclass
class ReflectionEngine:
    """Create reflective summaries from completed tasks."""

    def reflect(self, goal: str, evaluations: Iterable[EvaluationResult]) -> str:
        """Return a concise reflection string."""

        evaluations_list: List[EvaluationResult] = list(evaluations)
        if not evaluations_list:
            return f"Goal '{goal}' has no completed subtasks yet."
        average_score = sum(result.score for result in evaluations_list) / len(evaluations_list)
        status = "met" if average_score >= 0.6 else "needs improvement"
        return (
            f"Reflection on goal '{goal}': average score {average_score:.2f}; execution {status}."
        )
