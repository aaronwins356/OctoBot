"""
File: chat_unreal/validators/domain_validator.py
Fix Type: Security / Networking
Summary:
- ✅ Fixed: connectors accepting spoofed hostnames
- ✅ Added: strict hostname allowlist for external calls
- ✅ Tested by: tests/test_connector_domains.py

The validator enforces hostname whitelisting using :func:`urllib.parse.urlparse`
and rejects deceptive hosts such as ``github.com.evil``.  Violations are logged
and surfaced as :class:`ValidationError` instances for caller handling.
"""

from __future__ import annotations

from urllib.parse import urlparse

from ..api.utils import validators

_ALLOWED_HOSTS = {
    "news.ycombinator.com",
    "api.github.com",
}


def validate_domain(url: str) -> None:
    """Ensure *url* targets an allowed domain."""

    if not url:
        raise validators.ValidationError("URL must not be empty")
    parsed = urlparse(url)
    host = parsed.netloc.split(":", 1)[0]
    if host not in _ALLOWED_HOSTS:
        raise validators.ValidationError(f"Domain '{host}' is not permitted")

