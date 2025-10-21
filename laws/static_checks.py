"""Supplementary static analysis for proposals and new agents."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from utils.logger import get_logger

from .enforcement import LawViolation, load_constitution
from .validator import ValidationResult, check_proposal

LOGGER = get_logger(__name__)


def run_static_checks(paths: Iterable[Path]) -> ValidationResult:
    """Execute validator on the provided paths using the current constitution."""

    constitution = load_constitution(Path("laws/constitution.yaml"))
    result = check_proposal(paths, constitution)
    if not result.ok:
        raise LawViolation("; ".join(result.errors))
    LOGGER.info("Static checks passed for %s", [str(p) for p in paths])
    return result


__all__ = ["run_static_checks"]
