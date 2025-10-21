"""
File: octobot/core/orchestrator.py
Fix Type: Security / Workflow
Summary:
- ✅ Fixed: approval bypass without validator confirmation
- ✅ Added: per-instance event queue with cancellation-aware handlers
- ✅ Tested by: tests/test_orchestrator_validation.py

The orchestrator now verifies validation reports before applying proposals,
ensuring coverage remains above 90% and constitutional compliance is preserved.
Events are processed through an instance-specific queue, preventing cross-test
interference and allowing deterministic unit tests.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from octobot.agents.engineers.analyzer_agent import AnalyzerAgent
from octobot.agents.engineers.tester_agent import TesterAgent
from octobot.core.evaluator import Evaluation, Evaluator
from octobot.core.proposal_manager import Proposal, ProposalManager
from octobot.core.updater import Updater
from octobot.laws.validator import ValidationReport, validate_proposal
from octobot.memory.history_logger import MemoryStore
from octobot.memory.ledger import Ledger
from octobot.memory.logger import log_event
from octobot.memory.utils import timestamp

LOGGER = logging.getLogger(__name__)

EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass(frozen=True)
class Event:
    name: str
    payload: Dict[str, Any]
    created_at: str


class EventBus:
    """Async event bus with per-orchestrator queue."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._queue: "asyncio.Queue[Event]" = asyncio.Queue()
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._subscribers.setdefault(event_name, []).append(handler)

    async def publish(self, event_name: str, payload: Dict[str, Any]) -> Event:
        event = Event(name=event_name, payload=payload, created_at=timestamp())
        await self._queue.put(event)
        log_event("event_bus", "publish", event_name, payload)
        return event

    async def drain(self) -> None:
        while not self._queue.empty():
            event = await self._queue.get()
            handlers = list(self._subscribers.get(event.name, []))
            await self._dispatch(event, handlers)
            self._queue.task_done()

    async def _dispatch(self, event: Event, handlers: List[EventHandler]) -> None:
        tasks = [self._loop.create_task(handler(event)) for handler in handlers]
        if not tasks:
            return
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            for task in tasks:
                if task.cancelled():
                    LOGGER.warning("Handler task cancelled for event %s", event.name)


class Orchestrator:
    """Coordinate proposal lifecycle under constitutional constraints."""

    def __init__(
        self,
        analyzer: AnalyzerAgent | None = None,
        proposals: ProposalManager | None = None,
        evaluator: Evaluator | None = None,
        updater: Updater | None = None,
        tester: TesterAgent | None = None,
        ledger: Ledger | None = None,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.analyzer = analyzer or AnalyzerAgent()
        self.proposals = proposals or ProposalManager()
        self.evaluator = evaluator or Evaluator()
        self.updater = updater or Updater()
        self.tester = tester or TesterAgent()
        self.ledger = ledger or Ledger()
        self.store: MemoryStore = self.proposals.store
        self.bus = EventBus(self.loop)
        self._validation_reports: Dict[str, ValidationReport] = {}
        self._evaluation_scores: Dict[str, Evaluation] = {}
        self._applied_commits: Dict[str, str] = {}
        self._proposers: Dict[str, str] = {}
        self._register_handlers()

    def draft_proposal(self, topic: str, proposer: str = "engineers") -> Dict[str, Any]:
        return asyncio.run(self.async_draft_proposal(topic, proposer))

    async def async_draft_proposal(
        self, topic: str, proposer: str = "engineers"
    ) -> Dict[str, Any]:
        analysis = self.analyzer.scan_repo()
        proposal = self.proposals.generate(topic, analysis)
        self._proposers[proposal.proposal_id] = proposer
        await self.bus.publish(
            "proposal.created",
            {
                "proposal_id": proposal.proposal_id,
                "proposer": proposer,
                "analysis": analysis,
            },
        )
        await self.bus.drain()
        validation = self._validation_reports.get(proposal.proposal_id)
        evaluation = self._evaluation_scores.get(proposal.proposal_id)
        return {
            "proposal": proposal,
            "analysis": analysis,
            "validation": validation,
            "evaluation": evaluation,
        }

    def approve_proposal(self, proposal_id: str, approver: str) -> Optional[str]:
        return asyncio.run(self.async_approve_proposal(proposal_id, approver))

    async def async_approve_proposal(self, proposal_id: str, approver: str) -> Optional[str]:
        proposal = self.proposals.load(proposal_id)
        if not proposal:
            LOGGER.warning("Approval requested for unknown proposal %s", proposal_id)
            return None
        validation = await self._ensure_validation(proposal)
        if validation is None:
            LOGGER.error("Validation missing for %s; refusing approval", proposal_id)
            return None
        if not validation.compliant:
            log_event(
                "orchestrator",
                "approval_blocked",
                "violations",
                {"proposal": proposal_id, "issues": validation.issues},
            )
            return None
        if validation.coverage < 0.9:
            log_event(
                "orchestrator",
                "approval_blocked",
                "coverage",
                {"proposal": proposal_id, "coverage": validation.coverage},
            )
            return None
        test_results = self.tester.run_tests()
        status = str(test_results.get("status"))
        if status not in {"passed", "skipped"}:
            log_event(
                "orchestrator",
                "tests_failed",
                "blocked",
                {"proposal": proposal_id, "status": status},
            )
            return None
        try:
            commit = self.updater.apply(proposal)
        except Exception as error:  # pragma: no cover - defensive guard
            log_event(
                "orchestrator",
                "apply_failed",
                "error",
                {"proposal": proposal_id, "error": repr(error)},
            )
            return None
        self.proposals.approve(proposal_id, approver)
        self._applied_commits[proposal_id] = commit
        self.ledger.append(proposal, "approved", self._proposers.get(proposal_id, approver))
        self.store.log_history(
            "governance",
            "proposal_applied",
            f"{proposal_id}:{commit}:{approver}",
        )
        await self.bus.publish(
            "proposal.approved",
            {"proposal_id": proposal_id, "approver": approver, "commit": commit},
        )
        await self.bus.drain()
        return commit

    async def _ensure_validation(self, proposal: Proposal) -> Optional[ValidationReport]:
        report = self._validation_reports.get(proposal.proposal_id)
        if report is None:
            report = validate_proposal(proposal)
            self._validation_reports[proposal.proposal_id] = report
        if report.compliant and report.coverage >= 0.9:
            self.proposals.mark_ready_for_review(proposal.proposal_id, report.coverage)
        return report

    def _register_handlers(self) -> None:
        self.bus.subscribe("proposal.created", self._handle_created)
        self.bus.subscribe("proposal.validated", self._handle_validated)
        self.bus.subscribe("proposal.approved", self._handle_approved)

    async def _handle_created(self, event: Event) -> None:
        proposal_id = event.payload["proposal_id"]
        proposer = event.payload.get("proposer", "unknown")
        proposal = self.proposals.load(proposal_id)
        if not proposal:
            return
        self.ledger.append(proposal, "created", proposer)
        report = validate_proposal(proposal)
        self._validation_reports[proposal_id] = report
        payload = {
            "proposal_id": proposal_id,
            "report": {
                "compliant": report.compliant,
                "coverage": report.coverage,
                "issues": list(report.issues),
                "summary": report.summary,
            },
        }
        await self.bus.publish("proposal.validated", payload)

    async def _handle_validated(self, event: Event) -> None:
        proposal_id = event.payload["proposal_id"]
        data = event.payload.get("report", {})
        report = ValidationReport(
            proposal_id=proposal_id,
            compliant=bool(data.get("compliant", False)),
            issues=list(data.get("issues", [])),
            coverage=float(data.get("coverage", 0.0)),
            summary=str(data.get("summary", "")),
        )
        self._validation_reports[proposal_id] = report
        if report.compliant and report.coverage >= 0.9:
            self.proposals.mark_ready_for_review(proposal_id, report.coverage)
        self.proposals.mark_presented(proposal_id)
        proposal = self.proposals.load(proposal_id)
        if proposal:
            evaluations = self.evaluator.score(
                [
                    {
                        "id": proposal.proposal_id,
                        "summary": proposal.summary,
                        "coverage": report.coverage,
                    }
                ]
            )
            if evaluations:
                self._evaluation_scores[proposal_id] = evaluations[0]
        self.store.log_history("governance", "proposal_validated", proposal_id)

    async def _handle_approved(self, event: Event) -> None:
        proposal_id = event.payload["proposal_id"]
        approver = event.payload.get("approver", "unknown")
        commit = event.payload.get("commit", "")
        log_event(
            "orchestrator",
            "proposal_approved",
            "applied",
            {"proposal": proposal_id, "commit": commit, "approver": approver},
        )


__all__ = ["Event", "EventBus", "Orchestrator"]

