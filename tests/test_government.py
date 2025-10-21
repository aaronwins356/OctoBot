from __future__ import annotations

import json
from pathlib import Path

from octobot.core.orchestrator import Orchestrator
from octobot.laws.audit import ComplianceAudit
from octobot.memory.utils import repo_root


def test_orchestrator_generates_proposal(tmp_path: Path) -> None:
    orchestrator = Orchestrator()
    lifecycle = orchestrator.draft_proposal("Governance Hardening")
    assert lifecycle.proposal.path.exists()
    assert lifecycle.validation is not None and lifecycle.validation.compliant
    ledger_path = repo_root() / "memory" / "ledger.json"
    entries = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(entry["status"] == "validated" for entry in entries)


def test_compliance_audit_generates_report(tmp_path: Path) -> None:
    orchestrator = Orchestrator()
    orchestrator.draft_proposal("Audit Trail")
    auditor = ComplianceAudit()
    report = auditor.analyse()
    assert "generated_at" in report
    path = auditor.write_report()
    assert path.exists()
