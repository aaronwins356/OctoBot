"""Generate proposal documentation artefacts."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from octobot.laws.validator import enforce
from octobot.memory.logger import log_event


class DocumentorAgent:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def write_summary(self, proposal_dir: Path, context: Dict[str, str]) -> Path:
        document_path = proposal_dir / "SUMMARY.md"
        enforce("filesystem_write", str(document_path))
        content = "\n".join(
            [
                "# Proposal Summary",
                "",
                f"## Topic\n{context.get('topic', 'General maintenance')}",
                "",
                f"## Rationale\n{context.get('rationale', 'Automated suggestion based on analyzer report.')}",
                "",
                "## Highlights",
                f"- Impact: {context.get('impact', 'medium')}",
                f"- Risk: {context.get('risk', 'low')}",
                "",
                "## Notes",
                "This summary is generated for human review and must be approved before publication.",
            ]
        )
        proposal_dir.mkdir(parents=True, exist_ok=True)
        document_path.write_text(content, encoding="utf-8")
        log_event("documentor", "summary", "generated", document_path.as_posix())
        return document_path
