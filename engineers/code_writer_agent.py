"""Code rewrite suggestion engine for OctoBot."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List

from laws.validator import DEFAULT_VALIDATOR
from memory.history_logger import HistoryLogger


class CodeWriterAgent:
    def __init__(self, repo_root: Path | None = None, logger: HistoryLogger | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.logger = logger or HistoryLogger()

    def create_rewrite_candidates(self, report: Dict[str, List[Dict[str, str]]]) -> Path:
        DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
        proposals_root = self.repo_root / "proposals"
        proposals_root.mkdir(exist_ok=True)
        topic = "refactor" if report.get("findings") else "maintenance"
        proposal_id = f"{date.today().isoformat()}_{topic}"
        proposal_dir = proposals_root / proposal_id / "code"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        suggestions = []
        for finding in report.get("findings", [])[:5]:
            suggestion = {
                "file": finding["file_path"],
                "issue": finding["issue_type"],
                "recommendation": self._recommendation_for(finding),
            }
            suggestions.append(suggestion)
        if not suggestions:
            suggestions.append(
                {
                    "file": "README.md",
                    "issue": "documentation",
                    "recommendation": "Add clarification about project setup steps.",
                }
            )
        code_path = proposal_dir / "suggestions.json"
        code_path.write_text(json.dumps(suggestions, indent=2), encoding="utf-8")
        self.logger.log_event(f"Code writer produced {len(suggestions)} suggestions for {proposal_id}")
        return proposal_dir.parent

    def _recommendation_for(self, finding: Dict[str, str]) -> str:
        issue = finding.get("issue_type")
        if issue == "complexity":
            return "Break the function into smaller helpers and simplify branching logic."
        if issue == "repetition":
            return "Extract the repeated call pattern into a shared utility function."
        return "Review this section manually to determine the optimal adjustment."
