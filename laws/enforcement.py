"""Legal enforcement utilities for the AI Republic government.

This module enforces the constitution by combining static analysis and
configuration-based rules. It should be considered immutable at runtime.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import yaml

from utils.logger import get_logger
from utils.settings import SETTINGS

from . import __version__
from .validator import analyze_source, load_source_ast

LOGGER = get_logger(__name__)


class LawViolation(Exception):
    """Raised when agent code violates constitutional restrictions."""


class Constitution(BaseException):  # pragma: no cover - sentinel only
    pass


def load_constitution(path: Path) -> dict:
    """Load and return constitution YAML."""

    if not path.exists():
        raise FileNotFoundError(f"Constitution not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    LOGGER.debug("Constitution loaded: %s", data)
    return data


def _check_paths(agent_path: Path, allowed_dirs: Iterable[str]) -> None:
    canonical = agent_path.resolve()
    for allowed in allowed_dirs:
        if canonical.is_relative_to(Path(allowed).resolve()):
            return
    raise LawViolation(
        f"Agent path {agent_path} resolves outside allowed directories: {allowed_dirs}"
    )


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_agent_code(agent_path: Path) -> None:
    """Static-check the agent source for banned patterns. Raises LawViolation on failure."""

    constitution = load_constitution(Path(SETTINGS.runtime.constitution_path))
    allowed_dirs = constitution.get("allowed_directories", [])
    _check_paths(agent_path, allowed_dirs)

    tree = load_source_ast(agent_path)
    analyze_source(tree, constitution)

    LOGGER.info(
        "Verified agent %s (hash=%s) against enforcement v%s",
        agent_path,
        _hash_file(agent_path),
        __version__,
    )


def verify_agent_permissions(target_path: Path) -> None:
    """Ensure an agent is writing within the permitted sandbox directory."""

    allowed_roots = [Path(p).resolve() for p in SETTINGS.security.allowed_write_paths]
    canonical = target_path.resolve()
    if not any(canonical.is_relative_to(root) for root in allowed_roots):
        raise LawViolation(
            f"Attempted write to {canonical} outside allowed roots {allowed_roots}"
        )


__all__ = [
    "LawViolation",
    "load_constitution",
    "verify_agent_code",
    "verify_agent_permissions",
]
