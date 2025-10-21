"""Evaluator scoring proposals for OctoBot."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from utils_yaml import safe_load

from memory.history_logger import HistoryLogger
from memory.reporter import Reporter


@dataclass
class Evaluation:
    proposal_id: str
    complexity: float
    tests: float
    docs: float
    risk: float
    rationale: str


class Evaluator:
    def __init__(self, reporter: Reporter | None = None, logger: HistoryLogger | None = None) -> None:
        self.reporter = reporter or Reporter()
        self.logger = logger or HistoryLogger()

    def score(self, proposals: Iterable[Dict[str, str]]) -> List[Evaluation]:
        evaluations: List[Evaluation] = []
        for proposal in proposals:
            complexity_score = 0.8 if "refactor" in proposal["summary"].lower() else 0.6
            tests_score = 0.7 if "test" in proposal["summary"].lower() else 0.5
            docs_score = 0.9 if "documentation" in proposal["summary"].lower() else 0.6
            risk_score = 0.3 if proposal.get("risk", "low") == "low" else 0.6
            rationale = (
                "Complexity score based on anticipated refactor improvements; "
                "risk inferred from proposal metadata."
            )
            evaluations.append(
                Evaluation(
                    proposal_id=proposal["id"],
                    complexity=complexity_score,
                    tests=tests_score,
                    docs=docs_score,
                    risk=risk_score,
                    rationale=rationale,
                )
            )
        for evaluation in evaluations:
            self.logger.log_event(
                "Evaluator scored %s (complexity=%.2f, tests=%.2f, docs=%.2f, risk=%.2f)"
                % (evaluation.proposal_id, evaluation.complexity, evaluation.tests, evaluation.docs, evaluation.risk)
            )
            self.reporter.record_evaluator_scores(
                {
                    "complexity": evaluation.complexity,
                    "tests": evaluation.tests,
                    "docs": evaluation.docs,
                    "risk": evaluation.risk,
                }
            )
        return evaluations


def load_evaluations_from_yaml(path: Path) -> List[Evaluation]:
    data = safe_load(path.read_text(encoding="utf-8"))
    return [Evaluation(**item) for item in data]
