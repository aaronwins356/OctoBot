"""Improvement cycle orchestrator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from engineers.analyzer_agent import AnalyzerAgent
from government.evaluator import Evaluator
from government.proposal_manager import ProposalManager, Proposal
from interface.dashboard import DashboardContext
from memory.history_logger import HistoryLogger


@dataclass
class CycleResult:
    report_path: str
    proposals: List[Proposal]


class Orchestrator:
    def __init__(
        self,
        analyzer: AnalyzerAgent | None = None,
        proposal_manager: ProposalManager | None = None,
        evaluator: Evaluator | None = None,
        logger: HistoryLogger | None = None,
    ) -> None:
        self.analyzer = analyzer or AnalyzerAgent()
        self.proposal_manager = proposal_manager or ProposalManager()
        self.evaluator = evaluator or Evaluator()
        self.logger = logger or HistoryLogger()

    def run_cycle(self) -> CycleResult:
        report = self.analyzer.scan_repo()
        proposals = self.proposal_manager.generate(report)
        self.evaluator.score([proposal.__dict__ | {"id": proposal.proposal_id} for proposal in proposals])
        self.logger.log_event("Improvement cycle completed")
        return CycleResult(report_path="reports/analyzer_report.json", proposals=proposals)

    def build_dashboard_context(self) -> DashboardContext:
        proposals = self.proposal_manager.list_proposals()
        evaluations = self.evaluator.score([proposal.__dict__ | {"id": proposal.proposal_id} for proposal in proposals])
        return DashboardContext.from_data(proposals, evaluations)
