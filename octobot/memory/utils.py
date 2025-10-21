"""Utility helpers for persistent storage and path management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Set

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROPOSALS_DIR = _REPO_ROOT / "proposals"
_VENTURES_DIR = _REPO_ROOT / "ventures"
_AUDIT_LOG = _REPO_ROOT / "memory" / "audit.log"
_LOGS_DIR = _REPO_ROOT / "memory" / "logs"
_CONNECTOR_AUDIT = _REPO_ROOT / "memory" / "connector_audit.log"
_CONFIG_DIR = _REPO_ROOT / "config"
_SCAN_EXCLUSIONS = _CONFIG_DIR / "scan_exclusions.yaml"


def repo_root() -> Path:
    """Return the root path of the repository."""
    return _REPO_ROOT


def proposals_root() -> Path:
    """Directory that contains generated proposals."""
    return ensure_directory(_PROPOSALS_DIR)


def ventures_root() -> Path:
    """Directory reserved for future venture generation."""
    return ensure_directory(_VENTURES_DIR)


def audit_log_path() -> Path:
    """Path to the audit log file."""
    return ensure_directory(_AUDIT_LOG.parent) / _AUDIT_LOG.name


def connector_audit_path() -> Path:
    """Path to the external connector audit log."""

    return ensure_directory(_CONNECTOR_AUDIT.parent) / _CONNECTOR_AUDIT.name


def logs_root() -> Path:
    """Directory where structured logs are stored."""

    return ensure_directory(_LOGS_DIR)


def log_file_path(now: datetime | None = None) -> Path:
    """Return the structured log file path for *now* (defaults to current time)."""

    current = now or utc_now()
    filename = f"{current.date().isoformat()}.json"
    return logs_root() / filename


def ensure_directory(path: Path) -> Path:
    """Create *path* if it does not yet exist and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def utc_now() -> datetime:
    """Return the current UTC timestamp as a timezone-aware object."""
    return datetime.now(timezone.utc)


def timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return utc_now().isoformat()


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML document from *path*."""

    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def dump_yaml(data: Dict[str, Any], path: Path) -> None:
    """Serialise *data* as YAML at *path*."""

    ensure_directory(path.parent)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def within_directory(path: Path, directory: Path) -> bool:
    """Return True if *path* resides inside *directory*."""
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def load_scan_exclusions(defaults: Iterable[str] | None = None) -> Set[str]:
    """Load directory names that should be excluded from analyzer scans."""

    exclusions: Set[str] = set(defaults or [])
    if not _SCAN_EXCLUSIONS.exists():
        return exclusions
    data = yaml.safe_load(_SCAN_EXCLUSIONS.read_text(encoding="utf-8"))
    raw_entries: Iterable[str]
    if isinstance(data, dict):
        raw_entries = data.get("exclude", [])
    else:
        raw_entries = data
    entries: Iterable[str]
    if isinstance(raw_entries, str):
        entries = [raw_entries]
    elif isinstance(raw_entries, Iterable):
        entries = raw_entries
    else:
        entries = []
    for entry in entries:
        if isinstance(entry, str):
            trimmed = entry.strip()
            if trimmed:
                exclusions.add(trimmed)
    return exclusions
