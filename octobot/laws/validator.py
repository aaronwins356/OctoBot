"""Central law loading and runtime enforcement."""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Set

from octobot.memory.logger import log_event
from octobot.memory.utils import (
    audit_log_path,
    load_yaml,
    proposals_root,
    repo_root,
    timestamp,
    within_directory,
)

if False:  # pragma: no cover - typing helpers
    from octobot.core.proposal_manager import Proposal


class RuleViolationError(RuntimeError):
    """Raised when an operation violates a constitutional rule."""


@dataclass(frozen=True)
class Rule:
    name: str
    description: str


@dataclass(frozen=True)
class ValidationReport:
    proposal_id: str
    compliant: bool
    issues: List[str]
    coverage: float
    summary: str


_LAWS_DIR = Path(__file__).resolve().parent
_CONSTITUTION = _LAWS_DIR / "constitution.yaml"
_ETHICS = _LAWS_DIR / "ethics.yaml"
_TECH = _LAWS_DIR / "tech_standards.yaml"

_RULES: Dict[str, Rule] | None = None
_REGISTERED_AGENTS: Set[str] = set()


def _load_rules() -> Dict[str, Rule]:
    global _RULES
    if _RULES is None:
        raw = load_yaml(_CONSTITUTION)
        entries = raw.get("rules", {}) if isinstance(raw, dict) else {}
        _RULES = {
            name: Rule(name=name, description=str(description))
            for name, description in entries.items()
        }
    return _RULES


def register_agent(agent_name: str) -> None:
    """Mark *agent_name* as having passed the entry check."""

    _REGISTERED_AGENTS.add(agent_name)
    log_event("laws", "agent_register", "recorded", {"agent": agent_name})


def require_agent(agent_name: str) -> None:
    """Ensure *agent_name* registered before executing autonomous work."""

    rules = _load_rules()
    rule = rules.get("agent_entry")
    if rule is None:  # pragma: no cover - configuration guard
        return
    if agent_name not in _REGISTERED_AGENTS:
        log_event("laws", "agent_entry", "blocked", {"agent": agent_name})
        raise RuleViolationError(rule.description)


def guard(agent_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator ensuring the calling agent registered with the validator."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            require_agent(agent_name)
            return func(*args, **kwargs)

        return wrapper

    return decorator


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


def _check_filesystem(context: str) -> bool:
    target = Path(context)
    repo = repo_root()
    allowed = [
        proposals_root(),
        repo / "ventures",
        repo / "docs",
        repo / "memory",
    ]
    return any(within_directory(target, directory) for directory in allowed)


def _is_allowed(rule: Rule, context: str) -> bool:
    if rule.name == "external_request":
        return context.endswith("connectors/unreal_bridge.py")
    if rule.name == "filesystem_write":
        return _check_filesystem(context)
    if rule.name == "code_merge":
        return context.lower() == "approved"
    if rule.name == "agent_entry":
        return context in _REGISTERED_AGENTS
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


def _load_ethics() -> List[str]:
    data = load_yaml(_ETHICS)
    values = data.get("principles", []) if isinstance(data, dict) else []
    return [str(item) for item in values]


def _load_quality_gates() -> Dict[str, Any]:
    data = load_yaml(_TECH)
    quality: Dict[str, Any] = {}
    if isinstance(data, dict):
        raw = data.get("quality_gates", {})
        if isinstance(raw, dict):
            quality = raw
    return quality


def validate_proposal(proposal: "Proposal") -> ValidationReport:
    """Validate a proposal directory against constitutional requirements."""

    metadata_path = proposal.path / "proposal.yaml"
    rationale_path = proposal.path / "rationale.md"
    diff_path = proposal.path / "diff.patch"
    impact_path = proposal.path / "impact.json"
    issues: List[str] = []

    metadata = load_yaml(metadata_path)
    summary = str(metadata.get("summary", "")) if metadata else ""
    coverage = float(metadata.get("coverage", 0.0) or 0.0) if metadata else 0.0

    quality = _load_quality_gates()
    min_coverage = float(quality.get("min_coverage", 0.0) or 0.0)
    if coverage < min_coverage:
        issues.append(f"coverage below {int(min_coverage * 100)}% threshold")

    if metadata.get("id") != proposal.proposal_id:
        issues.append("proposal id mismatch")

    if quality.get("require_rationale", True) and not rationale_path.exists():
        issues.append("rationale.md is missing")
    if quality.get("require_diff", True) and not diff_path.exists():
        issues.append("diff.patch is missing")

    if not summary.strip():
        issues.append("proposal summary is empty")

    impact: Dict[str, Any] = {}
    if not impact_path.exists():
        issues.append("impact.json is missing")
    else:
        loaded_impact = json.loads(impact_path.read_text(encoding="utf-8"))
        if isinstance(loaded_impact, dict):
            impact = loaded_impact

    if impact and impact.get("risk") not in {"low", "medium", "high"}:
        issues.append("impact.json must define risk as low/medium/high")

    ethics = _load_ethics()
    for principle in ethics:
        if "transaction" in principle.lower() and impact.get("simulated_transactions"):
            issues.append("proposals must not include financial transactions")

    compliant = not issues
    log_event(
        "laws",
        "validate_proposal",
        "compliant" if compliant else "violations",
        {"proposal": proposal.proposal_id, "issues": issues, "coverage": coverage},
    )
    return ValidationReport(
        proposal_id=proposal.proposal_id,
        compliant=compliant,
        issues=issues,
        coverage=coverage,
        summary=summary,
    )


__all__ = [
    "RuleViolationError",
    "ValidationReport",
    "enforce",
    "guard",
    "register_agent",
    "require_agent",
    "validate_proposal",
]
