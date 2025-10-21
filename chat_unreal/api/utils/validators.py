"""Input validation helpers for Chat Unreal endpoints."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ... import config


@dataclass(slots=True)
class ValidationError(Exception):
    """Represents validation failures for incoming payloads."""

    message: str

    def __str__(self) -> str:  # pragma: no cover - dataclass convenience
        return self.message


_PAYLOAD_KEY_PATTERN = re.compile(r"^[a-z0-9_]+$")


def validate_payload(
    payload: dict[str, object] | None,
    *,
    required_fields: Iterable[str],
    optional_fields: Iterable[str] | None = None,
) -> dict[str, object]:
    """Validate a JSON payload for required/optional keys."""

    if payload is None:
        raise ValidationError("Missing JSON payload")

    optional = set(optional_fields or [])
    required = set(required_fields)
    allowed = required | optional

    for key in payload:
        if not isinstance(key, str) or not _PAYLOAD_KEY_PATTERN.match(key):
            raise ValidationError(f"Invalid payload key: {key!r}")
        if key not in allowed:
            raise ValidationError(f"Unexpected payload key: {key}")

    for field in required:
        if field not in payload:
            raise ValidationError(f"Missing required field: {field}")
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ValidationError(f"Field {field} must be a non-empty string")

    return payload


def validate_domain(url: str) -> None:
    """Ensure a URL belongs to an allowed domain."""

    for domain in config.ALLOWED_DOMAINS:
        if domain in url:
            return
    raise ValidationError(f"Domain not permitted: {url}")


def validate_endpoint(endpoint: str) -> None:
    """Ensure endpoint is whitelisted."""

    if endpoint not in config.DEFAULT_ALLOWED_ENDPOINTS:
        raise ValidationError(f"Endpoint not permitted: {endpoint}")
