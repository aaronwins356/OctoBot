"""Common helpers for hardened connector implementations."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from octobot.memory.logger import log_event
from octobot.memory.utils import connector_audit_path, timestamp

_ALLOWED_JSON_TYPES = {"application/json"}
_TEXT_CONTENT_PREFIX = "text/"
_SANITIZE_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_text(value: str, *, limit: int | None = None) -> str:
    """Remove control characters and optionally trim *value*."""

    cleaned = _SANITIZE_PATTERN.sub("", value).strip()
    if limit is not None and limit >= 0:
        return cleaned[:limit]
    return cleaned


def ensure_safe_content(content_type: str) -> None:
    """Validate *content_type* against the approved allow list."""

    media_type = content_type.split(";")[0].strip().lower()
    if media_type in _ALLOWED_JSON_TYPES:
        return
    if media_type.startswith(_TEXT_CONTENT_PREFIX):
        return
    raise ValueError(f"Unsafe content type: {content_type}")


def log_connector_call(name: str, url: str, status: str, metadata: Mapping[str, Any]) -> None:
    """Append a structured audit entry for connector traffic."""

    entry = {
        "time": timestamp(),
        "connector": name,
        "url": url,
        "status": status,
        "metadata": dict(metadata),
    }
    log_event(name, "connector_call", status, entry)
    log_path = connector_audit_path()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


__all__ = ["ensure_safe_content", "log_connector_call", "sanitize_text"]
