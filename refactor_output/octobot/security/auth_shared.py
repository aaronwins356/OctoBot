"""
File: octobot/security/auth_shared.py
Fix Type: Security / Authentication
Summary:
- ✅ Fixed: missing shared authentication enforcement across services
- ✅ Added: central token loader with strict validation for OCTOBOT_KEY
- ✅ Tested by: tests/test_auth_security.py

This module provides a shared authentication layer for both the Flask based
Chat Unreal API and the FastAPI dashboard. It verifies that the
``OCTOBOT_KEY`` environment variable is present and non-empty during startup
and exposes a decorator/helper that can be reused for request handlers.
The implementation keeps the authentication rules in a single location so
that the constitutional law of OctoBot can be enforced consistently.
"""

from __future__ import annotations

import functools
import hmac
import logging
from typing import Any, Callable, Dict, Optional

from octobot.config import env

LOGGER = logging.getLogger(__name__)


class AuthenticationError(RuntimeError):
    """Raised when a request fails constitutional authentication checks."""


def _load_expected_token() -> str:
    """Return the configured human approval token or raise an error.

    The validator fails closed: if ``OCTOBOT_KEY`` is missing or blank we raise
    an :class:`AuthenticationError`. This behaviour satisfies the security
    requirements introduced in the hardening summary.
    """

    token = env.get("OCTOBOT_KEY", default="")
    if not token or not token.strip():
        LOGGER.error("OCTOBOT_KEY is required for secure execution")
        raise AuthenticationError(
            "OCTOBOT_KEY environment variable must be configured before startup"
        )
    return token.strip()


def verify_token(candidate: Optional[str]) -> bool:
    """Return ``True`` if ``candidate`` matches the configured token.

    ``candidate`` is normalised to an empty string when ``None`` to protect
    against timing attacks caused by ``None`` comparisons.  Constant time
    comparisons are used to mitigate oracle style attacks.
    """

    expected = _load_expected_token()
    received = (candidate or "").strip()
    return hmac.compare_digest(expected.encode(), received.encode())


def require_human_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator enforcing human approval tokens on route handlers.

    The decorated call must provide a ``token`` keyword argument or include a
    request object that exposes headers containing ``x-octobot-key``.
    On failure an :class:`AuthenticationError` is raised.  Framework specific
    wrappers (Flask/FastAPI) can catch this error and translate it into a
    ``401`` or ``403`` response as appropriate.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = kwargs.pop("token", None)
        if token is None:
            request: Optional[Any] = kwargs.get("request")
            if request is not None:
                token = _extract_token_from_request(request)
        if not verify_token(token):
            LOGGER.warning("Rejected unauthorised call to %s", func.__name__)
            raise AuthenticationError("Invalid or missing OCTOBOT_KEY token")
        return func(*args, **kwargs)

    return wrapper


def _extract_token_from_request(request: Any) -> Optional[str]:
    """Extract the token from different request implementations."""

    if hasattr(request, "headers"):
        headers: Dict[str, str] = dict(request.headers)
        header_key = next(
            (k for k in headers if k.lower() == "x-octobot-key"),
            None,
        )
        if header_key:
            return headers[header_key]
    if hasattr(request, "cookies"):
        cookies: Dict[str, str] = getattr(request, "cookies")
        if isinstance(cookies, dict):
            return cookies.get("octobot-key")
    return None


def startup_guard() -> None:
    """Validate that the environment token is present before bootstrapping."""

    _load_expected_token()
    LOGGER.info("Authentication token validated during startup")

