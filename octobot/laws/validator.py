"""Rule enforcement utilities for OctoBot."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from octobot.core.proposal_manager import Proposal

from octobot.memory.logger import log_event
from octobot.memory.utils import (
    audit_log_path,
    load_yaml,
    proposals_root,
    repo_root,
    timestamp,
    within_directory,
)


class RuleViolationError(RuntimeError):
    """Raised when an operation violates a constitutional rule."""


@dataclass
class Rule:
    name: str
    description: str


@dataclass(frozen=True)
class ValidationReport:
    """Result of validating a proposal against the codified laws."""

    proposal_id: str
    compliant: bool
    issues: List[str]
    coverage: float
    summary: str


_CONSTITUTION_PATH = Path(__file__).resolve().parent / "constitution.yaml"
_RULES: Dict[str, Rule] | None = None


def _load_rules() -> Dict[str, Rule]:
    global _RULES
    if _RULES is None:
        raw = load_yaml(_CONSTITUTION_PATH)
        entries = raw.get("rules", {})
        if isinstance(entries, dict):
            _RULES = {name: Rule(name=name, description=str(desc)) for name, desc in entries.items()}
        else:
            raise ValueError("Constitution must define rules as a mapping of name to description")
    return _RULES


def _audit(status: str, rule: Rule, context: str) -> None:
    entry = {
        "time": timestamp(),
        "rule": rule.name,
        "status": status,
        "description": rule.description,
        "context": context,
    }
    log_path = audit_log_path()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _is_allowed(rule: Rule, context: str) -> bool:
    repo = repo_root()
    if rule.name == "external_request":
        return context.endswith("connectors/unreal_bridge.py")
    if rule.name == "filesystem_write":
        target = Path(context)
        return within_directory(target, proposals_root()) or within_directory(target, repo / "ventures")
    if rule.name == "code_merge":
        return context.lower() == "approved"
    return True


def enforce(rule_name: str, context: str) -> bool:
    """Log and enforce the rule named *rule_name* against *context*."""
    rules = _load_rules()
    if rule_name not in rules:
        raise RuleViolationError(f"Unknown rule '{rule_name}'")
    rule = rules[rule_name]
    allowed = _is_allowed(rule, context)
    status = "allowed" if allowed else "blocked"
    log_event("laws", f"enforce:{rule.name}", status, {"context": context})
    _audit(status, rule, context)
    if not allowed:
        raise RuleViolationError(rule.description)
    return True


def validate_proposal(proposal: "Proposal") -> ValidationReport:
    """Validate a proposal directory against constitutional requirements."""

    metadata_path = proposal.path / "proposal.yaml"
    rationale_path = proposal.path / "rationale.md"
    diff_path = proposal.path / "diff.patch"
    issues: List[str] = []

    metadata: Dict[str, object] = {}
    if not metadata_path.exists():
        issues.append("proposal.yaml is missing")
    else:
        loaded = load_yaml(metadata_path)
        if isinstance(loaded, dict):
            metadata = loaded
        if metadata.get("id") != proposal.proposal_id:
            issues.append("proposal id mismatch")

    summary = str(metadata.get("summary", "")) if metadata else ""
    coverage = float(metadata.get("coverage", 0.0)) if metadata else 0.0

    if coverage < 0.5:
        issues.append("coverage below 50% threshold")
    if not summary.strip():
        issues.append("proposal summary is empty")
    if not rationale_path.exists():
        issues.append("rationale.md is missing")
    if not diff_path.exists():
        issues.append("diff.patch is missing")

    compliant = not issues
    log_event(
        "laws",
        "validate_proposal",
        "compliant" if compliant else "violations",
        {"proposal": proposal.proposal_id, "issues": issues},
    )
    return ValidationReport(
        proposal_id=proposal.proposal_id,
        compliant=compliant,
        issues=issues,
        coverage=coverage,
        summary=summary,
    )
