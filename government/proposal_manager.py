"""Proposal management for OctoBot."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from utils_yaml import safe_dump, safe_load

from engineers.code_writer_agent import CodeWriterAgent
from engineers.documentor_agent import DocumentorAgent
from laws.validator import DEFAULT_VALIDATOR
from memory.history_logger import HistoryLogger


@dataclass
class Proposal:
    proposal_id: str
    impact: str
    risk: str
    summary: str
    rationale: str
    path: Path


class ProposalManager:
    def __init__(
        self,
        repo_root: Path | None = None,
        code_writer: CodeWriterAgent | None = None,
        documentor: DocumentorAgent | None = None,
        logger: HistoryLogger | None = None,
    ) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.code_writer = code_writer or CodeWriterAgent(self.repo_root)
        self.documentor = documentor or DocumentorAgent(self.repo_root)
        self.logger = logger or HistoryLogger()

    def generate(self, analyzer_report: Dict[str, List[Dict[str, str]]]) -> List[Proposal]:
        DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
        proposal_dir = self.code_writer.create_rewrite_candidates(analyzer_report)
        impact = "high" if analyzer_report.get("findings") else "medium"
        proposal_id = proposal_dir.name
        yaml_data = {
            "id": proposal_id,
            "impact": impact,
            "risk": "low",
            "summary": "Automated refactor suggestions based on analyzer findings",
            "rationale": "Analyzer detected opportunities to simplify logic and improve documentation.",
        }
        proposal_yaml = proposal_dir / "proposal.yaml"
        proposal_yaml.write_text(safe_dump(yaml_data, sort_keys=False), encoding="utf-8")
        self.documentor.write_summary(
            proposal_dir,
            {
                "topic": "Refactor import structure" if analyzer_report.get("unused_imports") else "Documentation improvements",
                "impact": yaml_data["impact"],
                "risk": yaml_data["risk"],
                "rationale": yaml_data["rationale"],
            },
        )
        self.logger.log_event(f"Proposal {proposal_id} generated")
        return [
            Proposal(
                proposal_id=yaml_data["id"],
                impact=yaml_data["impact"],
                risk=yaml_data["risk"],
                summary=yaml_data["summary"],
                rationale=yaml_data["rationale"],
                path=proposal_dir,
            )
        ]

    def list_proposals(self) -> List[Proposal]:
        proposals_root = self.repo_root / "proposals"
        proposals: List[Proposal] = []
        if not proposals_root.exists():
            return proposals
        for path in proposals_root.iterdir():
            yaml_path = path / "proposal.yaml"
            if yaml_path.exists():
                data = safe_load(yaml_path.read_text(encoding="utf-8"))
                proposals.append(
                    Proposal(
                        proposal_id=data["id"],
                        impact=data.get("impact", "medium"),
                        risk=data.get("risk", "medium"),
                        summary=data.get("summary", ""),
                        rationale=data.get("rationale", ""),
                        path=path,
                    )
                )
        proposals.sort(key=lambda p: p.proposal_id, reverse=True)
        return proposals

    def load_proposal(self, proposal_id: str) -> Proposal | None:
        for proposal in self.list_proposals():
            if proposal.proposal_id == proposal_id:
                return proposal
        return None
