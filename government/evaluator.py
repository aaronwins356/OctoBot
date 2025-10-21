"""Proposal evaluation heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from memory.logger import log_event


@dataclass
class Evaluation:
    proposal_id: str
    complexity: float
    tests: float
    docs: float
    risk: float
    rationale: str


class Evaluator:
    """Score proposals to help human reviewers."""

    def score(self, proposals: Iterable[Dict[str, object]]) -> List[Evaluation]:
        evaluations: List[Evaluation] = []
        for proposal in proposals:
            summary = str(proposal.get("summary", ""))
            coverage = float(proposal.get("coverage", 0.0))
            complexity = 0.8 if "refactor" in summary.lower() else 0.6
            tests = min(1.0, coverage / 100.0)
            docs = 0.9 if "doc" in summary.lower() else 0.6
            risk = 0.3 if coverage >= 90 else 0.5
            evaluation = Evaluation(
                proposal_id=str(proposal.get("id")),
                complexity=complexity,
                tests=tests,
                docs=docs,
                risk=risk,
                rationale="Heuristic scores derived from summary keywords and coverage.",
            )
            evaluations.append(evaluation)
            log_event(
                "evaluator",
                "score",
                "recorded",
                {
                    "proposal": evaluation.proposal_id,
                    "complexity": evaluation.complexity,
                    "tests": evaluation.tests,
                    "docs": evaluation.docs,
                    "risk": evaluation.risk,
                },
            )
        return evaluations
