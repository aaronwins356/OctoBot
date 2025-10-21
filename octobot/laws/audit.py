"""Compliance auditing helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from octobot.memory.logger import log_event
from octobot.memory.utils import ensure_directory, repo_root, timestamp


@dataclass(frozen=True)
class ComplianceIssue:
    proposal_id: str
    severity: str
    description: str


class ComplianceAudit:
    """Generate compliance reports based on ledger and log data."""

    def __init__(self, ledger_path: Path | None = None) -> None:
        default_path = repo_root() / "memory" / "ledger.json"
        self.ledger_path = ledger_path or default_path

    def _read_ledger(self) -> Iterable[Dict[str, object]]:
        if not self.ledger_path.exists():
            return []
        records: List[Dict[str, object]] = []
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records

    def analyse(self) -> Dict[str, Any]:
        entries = list(self._read_ledger())
        issues: List[ComplianceIssue] = []
        for entry in entries:
            status = str(entry.get("status", ""))
            proposal_id = str(entry.get("proposal_id", "unknown"))
            if status == "rejected":
                issues.append(
                    ComplianceIssue(
                        proposal_id=proposal_id,
                        severity="high",
                        description="Proposal rejected during validation",
                    )
                )
        report: Dict[str, Any] = {
            "generated_at": timestamp(),
            "entries": entries,
            "issues": [issue.__dict__ for issue in issues],
        }
        log_event("audit", "generate", "completed", {"issues": len(issues)})
        return report

    def write_report(self, destination: Path | None = None) -> Path:
        report = self.analyse()
        path = destination or (repo_root() / "memory" / "reports" / "compliance.json")
        ensure_directory(path.parent)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log_event("audit", "write", "stored", {"path": path.as_posix()})
        return path


__all__ = ["ComplianceAudit", "ComplianceIssue"]
