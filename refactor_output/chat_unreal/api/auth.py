"""
File: chat_unreal/api/auth.py
Fix Type: Security / Integration
Summary:
- ✅ Fixed: missing auth validation on Chat Unreal endpoints
- ✅ Added: token enforcement via shared auth module and startup guard
- ✅ Tested by: tests/test_auth_security.py

This module adapts the shared authentication helpers for the Flask application.
It exposes decorators that ensure every action requiring human approval is
protected by a validated ``OCTOBOT_KEY`` token while respecting OctoBot's
constitutional boundaries.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import abort, request

from octobot.security.auth_shared import (
    AuthenticationError,
    require_human_auth,
    startup_guard,
)

startup_guard()


def _translate_auth_error(func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a function to translate authentication errors into HTTP responses."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except AuthenticationError as exc:  # pragma: no cover - defensive guard
            abort(401, description=str(exc))

    return wrapper


def human_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Flask friendly decorator enforcing human authentication tokens."""

    @_translate_auth_error
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = request.headers.get("X-Octobot-Key") or request.args.get("token")
        guarded = require_human_auth(func)
        return guarded(*args, token=token, request=request, **kwargs)

    return wrapper

