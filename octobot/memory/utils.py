"""Utility helpers for persistent storage and path management."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROPOSALS_DIR = _REPO_ROOT / "proposals"
_VENTURES_DIR = _REPO_ROOT / "ventures"
_AUDIT_LOG = _REPO_ROOT / "memory" / "audit.log"


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
    """Load a lightweight YAML document from *path*."""
    if not path.exists():
        return {}
    data: Dict[str, Any] = {}
    current_section: Dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("-"):
            key = stripped[:-1].strip()
            current_section = {}
            data[key] = current_section
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        target = current_section if indent and current_section is not None else data
        key = key.strip()
        value_str = value.strip()
        if not value_str:
            target[key] = ""
            continue
        try:
            target[key] = json.loads(value_str)
        except json.JSONDecodeError:
            target[key] = value_str
    return data


def dump_yaml(data: Dict[str, Any], path: Path) -> None:
    """Serialise *data* as a YAML-like mapping at *path*."""
    ensure_directory(path.parent)
    lines = [f"{key}: {json.dumps(value)}" for key, value in data.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def within_directory(path: Path, directory: Path) -> bool:
    """Return True if *path* resides inside *directory*."""
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False
