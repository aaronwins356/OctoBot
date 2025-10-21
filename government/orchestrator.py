"""Finite state orchestrator for the proposal lifecycle."""
from __future__ import annotations

import enum
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from engineers.analyzer_agent import AnalyzerAgent
from government.proposal_manager import Proposal, ProposalManager
from government.updater import Updater
from memory.history_logger import MemoryStore
from memory.logger import log_event
from memory.utils import repo_root, timestamp


class CycleState(enum.Enum):
    ANALYZE = "analyze"
    PROPOSE = "propose"
    EVALUATE = "evaluate"
    PRESENT = "present"
    AWAIT_APPROVAL = "await_approval"
    APPLY = "apply"


@dataclass
class CycleTransition:
    from_state: CycleState
    to_state: CycleState
    occurred_at: str
    repo_sha: str


@dataclass
class CycleResult:
    proposal: Proposal
    transitions: List[CycleTransition]


class Orchestrator:
    """Manage the deterministic proposal cycle."""

    def __init__(
        self,
        analyzer: AnalyzerAgent | None = None,
        proposals: ProposalManager | None = None,
        store: MemoryStore | None = None,
        updater: Updater | None = None,
    ) -> None:
        self.analyzer = analyzer or AnalyzerAgent()
        self.proposals = proposals or ProposalManager()
        self.store = store or MemoryStore()
        self.updater = updater or Updater()

    def run_cycle(self, topic: str) -> CycleResult:
        transitions: List[CycleTransition] = []
        state = CycleState.ANALYZE
        analysis = self._analyze()
        transitions.append(self._transition(state, CycleState.PROPOSE))
        state = CycleState.PROPOSE
        proposal = self._propose(topic, analysis)
        transitions.append(self._transition(state, CycleState.EVALUATE))
        state = CycleState.EVALUATE
        self._evaluate(proposal, analysis)
        transitions.append(self._transition(state, CycleState.PRESENT))
        state = CycleState.PRESENT
        self._present(proposal)
        transitions.append(self._transition(state, CycleState.AWAIT_APPROVAL))
        state = CycleState.AWAIT_APPROVAL
        log_event("orchestrator", "await_approval", "pending", {"proposal": proposal.proposal_id})
        return CycleResult(proposal=proposal, transitions=transitions)

    def apply_if_approved(self, proposal_id: str) -> Optional[str]:
        proposal = self.proposals.load(proposal_id)
        if not proposal:
            return None
        record = self.store.fetch_proposal(proposal_id)
        if not record or record.status != "approved":
            return None
        log_event("orchestrator", "apply", "started", {"proposal": proposal_id})
        sha = self.updater.apply(proposal)
        log_event("orchestrator", "apply", "completed", {"proposal": proposal_id, "commit": sha})
        return sha

    def _analyze(self) -> Dict[str, object]:
        log_event("orchestrator", "analyze", "started", {})
        analysis = self.analyzer.scan_repo()
        log_event("orchestrator", "analyze", "completed", {"findings": len(analysis.get("findings", []))})
        return analysis

    def _propose(self, topic: str, analysis: Dict[str, object]) -> Proposal:
        log_event("orchestrator", "propose", "started", {"topic": topic})
        proposal = self.proposals.generate(topic, analysis)
        log_event("orchestrator", "propose", "completed", {"proposal": proposal.proposal_id})
        return proposal

    def _evaluate(self, proposal: Proposal, analysis: Dict[str, object]) -> None:
        coverage = float(analysis.get("coverage", 0.0)) * 100
        if coverage >= 90.0:
            self.proposals.mark_ready_for_review(proposal.proposal_id, coverage)
        log_event("orchestrator", "evaluate", "completed", {"proposal": proposal.proposal_id, "coverage": coverage})

    def _present(self, proposal: Proposal) -> None:
        self.proposals.mark_presented(proposal.proposal_id)
        log_event("orchestrator", "present", "queued", {"proposal": proposal.proposal_id})

    def _transition(self, from_state: CycleState, to_state: CycleState) -> CycleTransition:
        sha = self._current_sha()
        transition = CycleTransition(
            from_state=from_state,
            to_state=to_state,
            occurred_at=timestamp(),
            repo_sha=sha,
        )
        log_event(
            "orchestrator",
            "transition",
            "completed",
            {
                "from": from_state.value,
                "to": to_state.value,
                "sha": sha,
            },
        )
        return transition

    def _current_sha(self) -> str:
        try:
            sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root()).decode().strip()
        except subprocess.CalledProcessError:
            sha = "unknown"
        return sha
