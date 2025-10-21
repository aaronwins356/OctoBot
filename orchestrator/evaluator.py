"""Evaluation heuristics for ranking module outputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class EvaluationResult:
    """A scored evaluation for a candidate response."""

    content: str
    score: float
    rationale: str


class Evaluator:
    """Scores candidate responses using lightweight heuristics."""

    def __init__(self, threshold: float = 0.6) -> None:
        self.threshold = threshold

    def rank(self, candidates: Iterable[str], reference: str) -> List[EvaluationResult]:
        """Rank responses by comparing them to the reference text."""

        results: List[EvaluationResult] = []
        for candidate in candidates:
            score = self._similarity(candidate, reference)
            rationale = (
                "High lexical overlap" if score >= self.threshold else "Needs refinement"
            )
            results.append(EvaluationResult(content=candidate, score=score, rationale=rationale))
        results.sort(key=lambda result: result.score, reverse=True)
        return results

    @staticmethod
    def _similarity(candidate: str, reference: str) -> float:
        """Compute a simple Jaccard similarity between candidate and reference."""

        candidate_tokens = set(token.lower() for token in candidate.split())
        reference_tokens = set(token.lower() for token in reference.split())
        if not candidate_tokens or not reference_tokens:
            return 0.0
        intersection = len(candidate_tokens & reference_tokens)
        union = len(candidate_tokens | reference_tokens)
        return intersection / union

    def passes_threshold(self, score: float) -> bool:
        """Return True when the score satisfies the evaluator threshold."""

        return score >= self.threshold
