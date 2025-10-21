"""Compile evaluated proposals into summary artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from government.evaluator import Evaluation
from government.proposal_manager import Proposal


class Compiler:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def export(self, proposals: Iterable[Proposal], evaluations: Iterable[Evaluation]) -> Path:
        data = {
            "proposals": [
                {
                    "id": proposal.proposal_id,
                    "impact": proposal.impact,
                    "risk": proposal.risk,
                    "summary": proposal.summary,
                    "rationale": proposal.rationale,
                }
                for proposal in proposals
            ],
            "evaluations": [
                {
                    "proposal_id": evaluation.proposal_id,
                    "complexity": evaluation.complexity,
                    "tests": evaluation.tests,
                    "docs": evaluation.docs,
                    "risk": evaluation.risk,
                    "rationale": evaluation.rationale,
                }
                for evaluation in evaluations
            ],
        }
        target_dir = self.repo_root / "reports"
        target_dir.mkdir(exist_ok=True)
        path = target_dir / "compiled_summary.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path
