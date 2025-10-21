"""Asynchronous event orchestrator for proposal lifecycles."""
from __future__ import annotations

import asyncio
import inspect
import os
from dataclasses import asdict, dataclass
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

EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass(frozen=True)
class Event:
    name: str
    payload: Dict[str, Any]
    created_at: str


@dataclass
class ProposalLifecycle:
    proposal: Proposal
    analysis: Dict[str, Any]
    validation: Optional[ValidationReport]
    evaluation: Optional[Evaluation]


class EventBus:
    """Simple asyncio-backed event dispatcher."""

    def __init__(self) -> None:
        self._queue: "asyncio.Queue[Event]" = asyncio.Queue()
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler | Callable[[Event], None]) -> None:
        self._subscribers.setdefault(event_name, []).append(self._ensure_async(handler))

    async def publish(self, event_name: str, payload: Dict[str, Any]) -> Event:
        event = Event(name=event_name, payload=payload, created_at=timestamp())
        await self._queue.put(event)
        log_event("event_bus", "publish", event_name, payload)
        return event

    async def flush(self) -> None:
        while not self._queue.empty():
            event = await self._queue.get()
            handlers = list(self._subscribers.get(event.name, []))
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as error:  # pragma: no cover - defensive
                    log_event(
                        "event_bus",
                        "handler_error",
                        event.name,
                        {"error": repr(error)},
                    )
            self._queue.task_done()

    def _ensure_async(self, handler: EventHandler | Callable[[Event], None]) -> EventHandler:
        if inspect.iscoroutinefunction(handler):
            return handler  # type: ignore[return-value]

        async def wrapper(event: Event) -> None:
            handler(event)

        return wrapper


class Orchestrator:
    """Coordinate agents across the proposal lifecycle."""

    def __init__(
        self,
        analyzer: AnalyzerAgent | None = None,
        proposals: ProposalManager | None = None,
        evaluator: Evaluator | None = None,
        updater: Updater | None = None,
        tester: TesterAgent | None = None,
        ledger: Ledger | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self.analyzer = analyzer or AnalyzerAgent()
        self.proposals = proposals or ProposalManager()
        self.evaluator = evaluator or Evaluator()
        self.updater = updater or Updater()
        self.tester = tester or TesterAgent()
        self.ledger = ledger or Ledger()
        self.bus = bus or EventBus()
        self.store: MemoryStore = self.proposals.store
        self._validation_reports: Dict[str, ValidationReport] = {}
        self._evaluation_scores: Dict[str, Evaluation] = {}
        self._applied_commits: Dict[str, str] = {}
        self._proposers: Dict[str, str] = {}
        self._register_handlers()

    def draft_proposal(self, topic: str, proposer: str = "engineers") -> ProposalLifecycle:
        """Run analysis, generate a proposal, and trigger validation."""

        return asyncio.run(self.async_draft_proposal(topic, proposer))

    async def async_draft_proposal(self, topic: str, proposer: str = "engineers") -> ProposalLifecycle:
        analysis = self.analyzer.scan_repo()
        proposal = self.proposals.generate(topic, analysis)
        self._proposers[proposal.proposal_id] = proposer
        self.store.log_history("orchestrator", "proposal_created", proposal.proposal_id)
        await self.bus.publish(
            "proposal.created",
            {"proposal_id": proposal.proposal_id, "proposer": proposer, "analysis": analysis},
        )
        await self.bus.flush()
        validation = self._validation_reports.get(proposal.proposal_id)
        evaluation = self._evaluation_scores.get(proposal.proposal_id)
        return ProposalLifecycle(
            proposal=proposal,
            analysis=analysis,
            validation=validation,
            evaluation=evaluation,
        )

    def approve_proposal(self, proposal_id: str, approver: str) -> Optional[str]:
        """Mark *proposal_id* as approved and attempt to apply the changes."""

        return asyncio.run(self.async_approve_proposal(proposal_id, approver))

    async def async_approve_proposal(self, proposal_id: str, approver: str) -> Optional[str]:
        proposal = self.proposals.load(proposal_id)
        if not proposal:
            return None
        self.proposals.approve(proposal_id, approver)
        await self.bus.publish(
            "proposal.approved",
            {"proposal_id": proposal_id, "approver": approver},
        )
        await self.bus.flush()
        return self._applied_commits.get(proposal_id)

    def _register_handlers(self) -> None:
        self.bus.subscribe("proposal.created", self._handle_created)
        self.bus.subscribe("proposal.validated", self._handle_validated)
        self.bus.subscribe("proposal.approved", self._handle_approved)

    async def _handle_created(self, event: Event) -> None:
        proposal_id = event.payload["proposal_id"]
        proposer = event.payload.get("proposer", self._proposers.get(proposal_id, "unknown"))
        proposal = self.proposals.load(proposal_id)
        if not proposal:
            return
        self.ledger.append(proposal, "created", proposer)
        report = validate_proposal(proposal)
        self._validation_reports[proposal_id] = report
        if report.compliant:
            self.ledger.append(proposal, "validated", proposer)
            await self.bus.publish(
                "proposal.validated",
                {
                    "proposal_id": proposal_id,
                    "report": asdict(report),
                    "proposer": proposer,
                },
            )
        else:
            self.ledger.append(proposal, "rejected", proposer)
            log_event(
                "orchestrator",
                "proposal_validation_failed",
                "rejected",
                {"proposal": proposal_id, "issues": report.issues},
            )

    async def _handle_validated(self, event: Event) -> None:
        proposal_id = event.payload["proposal_id"]
        proposer = event.payload.get("proposer", self._proposers.get(proposal_id, "unknown"))
        data = event.payload.get("report", {})
        report = ValidationReport(
            proposal_id=proposal_id,
            compliant=bool(data.get("compliant", False)),
            issues=list(data.get("issues", [])),
            coverage=float(data.get("coverage", 0.0)),
            summary=str(data.get("summary", "")),
        )
        self._validation_reports[proposal_id] = report
        if not report.compliant:
            return
        coverage_percent = report.coverage * 100.0
        if coverage_percent >= 90.0:
            self.proposals.mark_ready_for_review(proposal_id, coverage_percent)
        self.proposals.mark_presented(proposal_id)
        proposal = self.proposals.load(proposal_id)
        if not proposal:
            return
        evaluations = self.evaluator.score(
            [
                {
                    "id": proposal.proposal_id,
                    "summary": proposal.summary,
                    "coverage": coverage_percent,
                }
            ]
        )
        evaluation = evaluations[0] if evaluations else None
        if evaluation:
            self._evaluation_scores[proposal_id] = evaluation
            log_event(
                "orchestrator",
                "proposal_evaluated",
                "scored",
                {
                    "proposal": proposal_id,
                    "complexity": evaluation.complexity,
                    "tests": evaluation.tests,
                    "docs": evaluation.docs,
                    "risk": evaluation.risk,
                },
            )
        self.store.log_history("governance", "proposal_validated", proposal_id)

    async def _handle_approved(self, event: Event) -> None:
        proposal_id = event.payload["proposal_id"]
        proposer = self._proposers.get(proposal_id, "unknown")
        approver = event.payload.get("approver", "unknown")
        proposal = self.proposals.load(proposal_id)
        if not proposal:
            return
        test_results = self.tester.run_tests()
        status = str(test_results.get("status"))
        if status not in {"passed", "skipped"}:
            log_event(
                "orchestrator",
                "tests_failed",
                "blocked",
                {
                    "proposal": proposal_id,
                    "status": status,
                    "returncode": test_results.get("returncode"),
                },
            )
            return
        if status == "skipped":
            log_event(
                "orchestrator",
                "tests_skipped",
                "warning",
                {"proposal": proposal_id},
            )
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("OCTOBOT_DRY_RUN"):
            commit = "dry-run"
        else:
            try:
                commit = self.updater.apply(proposal)
            except Exception as error:  # pragma: no cover - defensive
                log_event(
                    "orchestrator",
                    "apply_failed",
                    "error",
                    {"proposal": proposal_id, "error": repr(error)},
                )
                return
        self._applied_commits[proposal_id] = commit
        self.ledger.append(proposal, "approved", proposer)
        self.store.log_history(
            "governance",
            "proposal_applied",
            f"{proposal_id}:{commit}:{approver}",
        )
        log_event(
            "orchestrator",
            "proposal_approved",
            "applied",
            {"proposal": proposal_id, "commit": commit, "approver": approver},
        )


__all__ = ["Event", "EventBus", "Orchestrator", "ProposalLifecycle"]
