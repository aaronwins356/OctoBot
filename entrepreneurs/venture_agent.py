"""Entrepreneurial engine that drafts new digital venture proposals."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from entrepreneurs.base_agent import BaseAgent
from entrepreneurs.marketer_agent import MarketerAgent
from entrepreneurs.optimizer_agent import OptimizerAgent
from government.proposal_manager import VentureProposal, save_proposal
from memory import analytics
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class VentureAgent(BaseAgent):
    """Generates structured venture proposals for human review."""

    def __init__(self, name: str, sandbox_path: str) -> None:
        super().__init__(name, sandbox_path)
        self.optimizer = OptimizerAgent()
        self.marketer = MarketerAgent()
        self.metrics: List[analytics.TrafficMetric] = []

    def setup(self) -> None:
        LOGGER.info("Loading traffic metrics for venture ideation")
        self.metrics = analytics.load_metrics()

    def _affiliate_blog_proposal(self) -> VentureProposal:
        LOGGER.debug("Synthesising affiliate blog proposal using %d metrics", len(self.metrics))
        proposal = VentureProposal(
            proposal_id=datetime.utcnow().strftime("%Y%m%d%H%M"),
            proposal_name="Grounded Affiliate Blog",
            author_agent=self.name,
            description=(
                "A wellness-focused affiliate content hub that curates grounded lifestyle"
                " advice and product recommendations with full human editorial oversight."
            ),
            expected_cost="$0-$25 for hosting",
            expected_revenue="$50-150/month after 3 months",
            strategy=(
                "Publish weekly long-form articles optimised for ethical SEO, integrating"
                " affiliate partnerships only after human approval."
            ),
            ethical_statement=(
                "All affiliate suggestions will prioritise user wellbeing, contain disclosure"
                " language, and avoid manipulative calls-to-action."
            ),
            files_created=[
                "website/templates/home.html",
                "website/app.py",
            ],
            status="draft",
        )
        proposal.created_at = datetime.utcnow()
        return proposal

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        LOGGER.info("Generating affiliate blog proposal bundle")
        proposal = self._affiliate_blog_proposal()
        manifest_path = save_proposal(proposal)
        technical = self.optimizer.suggest_stack("affiliate_blog")
        marketing = self.marketer.seo_playbook("grounded lifestyle wellness")
        LOGGER.info("Proposal stored at %s", manifest_path.parent)
        return {
            "proposal_manifest": str(manifest_path),
            "technical_recommendations": [rec.__dict__ for rec in technical],
            "marketing_playbook": [idea.__dict__ for idea in marketing],
        }

    def report(self) -> Dict[str, Any]:
        return {
            "metrics_considered": [metric.model_dump() for metric in self.metrics],
        }


__all__ = ["VentureAgent"]
