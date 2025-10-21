"""Authentication helpers for Chat Unreal."""

from __future__ import annotations

import hmac
import os
from typing import Optional

from .. import config


def verify_request(token: Optional[str]) -> bool:
    """Verify that the provided token matches the configured secret."""

    expected = config.get_env_variable("OCTOBOT_KEY", "") or ""
    received = token or ""
    return hmac.compare_digest(expected.encode(), received.encode())


def require_token() -> str:
    """Return the configured API token or raise an error if missing."""

    token = config.get_env_variable("OCTOBOT_KEY")
    if not token:
        raise RuntimeError(
            "OCTOBOT_KEY environment variable must be set for authentication"
        )
    return token
