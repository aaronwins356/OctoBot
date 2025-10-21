"""Technical optimisation utilities for venture planning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TechnicalRecommendation:
    """Represents a suggested technical capability for a venture."""

    title: str
    description: str


class OptimizerAgent:
    """Provides lightweight technical recommendations to other agents."""

    name: str = "optimizer_agent"

    def suggest_stack(self, vertical: str) -> List[TechnicalRecommendation]:
        """Return high-level tooling recommendations for the venture vertical."""

        stack: Dict[str, List[TechnicalRecommendation]] = {
            "affiliate_blog": [
                TechnicalRecommendation(
                    title="Static Site Generation",
                    description="Use Flask with Jinja2 templates for transparent, reviewable builds.",
                ),
                TechnicalRecommendation(
                    title="Content Scheduler",
                    description="Schedule weekly article drafts via cron-compatible scripts to respect human oversight.",
                ),
                TechnicalRecommendation(
                    title="Analytics Hooks",
                    description="Integrate privacy-first analytics such as Plausible once explicitly approved.",
                ),
            ]
        }
        return stack.get(vertical, [])


__all__ = ["OptimizerAgent", "TechnicalRecommendation"]
