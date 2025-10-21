"""Generate placeholder rewrite candidates."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List

from laws.validator import enforce
from memory.logger import log_event
from memory.utils import proposals_root


class CodeWriterAgent:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def create_rewrite_candidates(self, report: Dict[str, List[Dict[str, str]]]) -> Path:
        topic = "refactor" if report.get("findings") else "maintenance"
        proposal_dir = proposals_root() / f"{date.today().isoformat()}_{topic}" / "code"
        enforce("filesystem_write", str(proposal_dir))
        proposal_dir.mkdir(parents=True, exist_ok=True)
        suggestions = [
            {
                "file": finding.get("file_path", ""),
                "issue": finding.get("issue_type", ""),
                "recommendation": self._recommendation_for(finding),
            }
            for finding in report.get("findings", [])[:5]
        ]
        if not suggestions:
            suggestions.append(
                {
                    "file": "README.md",
                    "issue": "documentation",
                    "recommendation": "Document setup steps for new contributors.",
                }
            )
        suggestions_path = proposal_dir / "suggestions.json"
        enforce("filesystem_write", str(suggestions_path))
        suggestions_path.write_text(json.dumps(suggestions, indent=2), encoding="utf-8")
        log_event(
            "code_writer",
            "suggestions",
            "generated",
            {"count": len(suggestions), "path": suggestions_path.as_posix()},
        )
        return proposal_dir.parent

    def _recommendation_for(self, finding: Dict[str, str]) -> str:
        issue = finding.get("issue_type")
        if issue == "complexity":
            return "Refactor into helper functions to reduce branching."
        if issue == "todo":
            return "Clarify outstanding TODO and plan resolution."
        return "Review this item manually for the optimal adjustment."
