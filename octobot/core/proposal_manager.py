"""Proposal management for OctoBot."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, cast

from octobot.laws.validator import enforce
from octobot.memory.history_logger import MemoryStore, ProposalRecord
from octobot.memory.logger import log_event
from octobot.memory.utils import dump_yaml, load_yaml, proposals_root, timestamp


@dataclass
class Proposal:
    proposal_id: str
    topic: str
    status: str
    path: Path
    summary: str
    coverage: float


class ProposalManager:
    """Create and retrieve proposals."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def generate(self, topic: str, analysis: Dict[str, Any]) -> Proposal:
        proposal_id = self._make_identifier(topic)
        proposal_dir = proposals_root() / proposal_id
        enforce("filesystem_write", str(proposal_dir))
        proposal_dir.mkdir(parents=True, exist_ok=True)
        findings_source = cast(Sequence[Any], analysis.get("findings", []))
        summary_text = f"Improve {topic} to address {len(findings_source)} findings."
        metadata: Dict[str, Any] = {
            "id": proposal_id,
            "topic": topic,
            "status": "draft",
            "created_at": timestamp(),
            "summary": summary_text,
            "coverage": analysis.get("coverage", 0.0),
        }
        metadata_path = proposal_dir / "proposal.yaml"
        enforce("filesystem_write", str(metadata_path))
        dump_yaml(metadata, metadata_path)
        tests_dir = proposal_dir / "tests"
        enforce("filesystem_write", str(tests_dir))
        tests_dir.mkdir(exist_ok=True)
        rationale_path = proposal_dir / "rationale.md"
        enforce("filesystem_write", str(rationale_path))
        rationale_path.write_text(
            self._compose_rationale(topic, analysis),
            encoding="utf-8",
        )
        diff_path = proposal_dir / "diff.patch"
        enforce("filesystem_write", str(diff_path))
        diff_path.write_text(self._compose_patch_stub(proposal_id, topic), encoding="utf-8")
        impact_path = proposal_dir / "impact.json"
        enforce("filesystem_write", str(impact_path))
        impact_path.write_text(
            json.dumps(self._compose_impact(metadata, analysis), indent=2),
            encoding="utf-8",
        )
        self.store.upsert_proposal(
            ProposalRecord(
                proposal_id=proposal_id,
                topic=topic,
                status="draft",
                created_at=metadata["created_at"],
                path=str(proposal_dir),
                approval_date=None,
            )
        )
        log_event("proposals", "generate", "draft", metadata)
        return Proposal(
            proposal_id=proposal_id,
            topic=topic,
            status="draft",
            path=proposal_dir,
            summary=summary_text,
            coverage=float(metadata["coverage"]),
        )

    def list_proposals(self) -> List[Proposal]:
        records = self.store.list_proposals()
        proposals: List[Proposal] = []
        for record in records:
            path = Path(record.path)
            yaml_path = path / "proposal.yaml"
            if not yaml_path.exists():
                continue
            data = load_yaml(yaml_path)
            data.setdefault("status", record.status)
            proposals.append(
                Proposal(
                    proposal_id=data["id"],
                    topic=data["topic"],
                    status=str(data.get("status", record.status)),
                    path=path,
                    summary=data.get("summary", ""),
                    coverage=float(data.get("coverage", 0.0)),
                )
            )
        return proposals

    def load(self, proposal_id: str) -> Proposal | None:
        for proposal in self.list_proposals():
            if proposal.proposal_id == proposal_id:
                return proposal
        return None

    def mark_ready_for_review(self, proposal_id: str, coverage: float) -> None:
        if coverage < 90.0:
            raise ValueError("Test coverage must be at least 90% before review")
        self.store.update_proposal_status(proposal_id, "ready", None)
        self._update_metadata(proposal_id, {"status": "ready", "coverage": coverage})
        log_event("proposals", "ready", "queued", {"proposal": proposal_id, "coverage": coverage})

    def mark_presented(self, proposal_id: str) -> None:
        self.store.update_proposal_status(proposal_id, "awaiting_approval", None)
        self._update_metadata(proposal_id, {"status": "awaiting_approval"})

    def approve(self, proposal_id: str, approver: str) -> None:
        approval_time = timestamp()
        self.store.update_proposal_status(proposal_id, "approved", approval_time)
        self._update_metadata(proposal_id, {"status": "approved", "approval_date": approval_time})
        log_event(
            "governance", "approve", "approved", {"proposal": proposal_id, "approver": approver}
        )

    def _make_identifier(self, topic: str) -> str:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        safe_topic = "_".join(part for part in topic.lower().split() if part)
        return f"{today}_{safe_topic}" if safe_topic else f"{today}_proposal"

    def _compose_rationale(self, topic: str, analysis: Dict[str, Any]) -> str:
        lines = [
            f"# Rationale for {topic}",
            "",
            "## Context",
            f"- Findings analysed: {len(cast(Sequence[Any], analysis.get('findings', [])))}",
            f"- Average complexity: {float(analysis.get('complexity_average', 0) or 0):.2f}",
            f"- TODO markers: {int(analysis.get('todos', 0) or 0)}",
            "",
            "## Proposed Approach",
            "The system will refactor modules to reduce complexity and improve documentation.",
            "All changes are staged within the proposals workspace for human review.",
        ]
        return "\n".join(lines)

    def _compose_patch_stub(self, proposal_id: str, topic: str) -> str:
        return (
            "--- /dev/null\n"
            f"+++ b/proposals/{proposal_id}/NOTES.md\n"
            "@@\n"
            f"+# Proposed improvements for {topic}\n"
            "+This placeholder file summarises intended changes.\n"
        )

    def _compose_impact(self, metadata: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        complexity_penalty = float(analysis.get("complexity_average", 0.0) or 0.0)
        findings_source = cast(Sequence[Any], analysis.get("findings", []))
        findings = len(findings_source)
        roi = max(1.0, findings * 1.5) / max(1.0, complexity_penalty + 1)
        return {
            "proposal_id": metadata["id"],
            "purpose": metadata.get("summary", ""),
            "expected_coverage": float(analysis.get("coverage", 0.0) or 0.0),
            "risk": "low" if complexity_penalty < 10 else "medium",
            "roi": round(roi, 2),
            "benefits": {
                "complexity_reduction": max(0, findings),
                "documentation_improvement": int(analysis.get("missing_docstrings", 0) or 0),
            },
        }

    def _update_metadata(self, proposal_id: str, updates: Dict[str, Any]) -> None:
        proposal = self.load(proposal_id)
        if not proposal:
            return
        metadata_path = proposal.path / "proposal.yaml"
        enforce("filesystem_write", str(metadata_path))
        data = load_yaml(metadata_path)
        data.update(updates)
        dump_yaml(data, metadata_path)
