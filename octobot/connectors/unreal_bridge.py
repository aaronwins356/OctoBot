"""Thin REST connector for the Chat Unreal reasoning service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

import httpx

from octobot.connectors.utils import ensure_safe_content, log_connector_call, sanitize_text
from octobot.laws.validator import enforce, law_enforced
from octobot.memory.logger import log_event

DEFAULT_URL = os.environ.get("OCTOBOT_UNREAL_URL", "http://127.0.0.1:8800/query")
_TIMEOUT = float(os.environ.get("OCTOBOT_UNREAL_TIMEOUT", "5.0"))
_MAX_RETRIES = int(os.environ.get("OCTOBOT_UNREAL_RETRIES", "2"))


class UnrealBridgeError(RuntimeError):
    """Raised when the Chat Unreal service cannot be reached."""


@dataclass(frozen=True)
class UnrealResponse:
    """Normalized response payload returned from Chat Unreal."""

    prompt: str
    text: str
    source: str


@law_enforced("external_request")
def query_unreal(prompt: str) -> str:
    """Send *prompt* to the Chat Unreal service and return the response text."""

    enforce("external_request", __file__)
    payload = {"prompt": prompt}
    headers = {"Content-Type": "application/json"}
    last_error: BaseException | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                response = client.post(DEFAULT_URL, json=payload, headers=headers)
            content_type = response.headers.get("Content-Type", "application/json")
            ensure_safe_content(content_type)
            log_connector_call(
                "unreal_bridge",
                DEFAULT_URL,
                "success",
                {"status_code": response.status_code, "attempt": attempt},
            )
            body = sanitize_text(response.text, limit=4096)
            data: Dict[str, Any]
            if content_type.split(";")[0].strip().lower() == "application/json":
                data = response.json()
            else:
                data = {"response": body}
            text = str(data.get("response") or data.get("message") or "").strip()
            if not text:
                log_event("unreal_bridge", "query", "empty", {})
                return _fallback(prompt).text
            log_event("unreal_bridge", "query", "ok", {"length": len(text)})
            return text
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            log_connector_call(
                "unreal_bridge",
                DEFAULT_URL,
                "error",
                {"attempt": attempt, "error": repr(exc)},
            )
    if last_error is not None:
        log_event("unreal_bridge", "query", "offline", {"error": repr(last_error)})
    return _fallback(prompt).text


def _fallback(prompt: str) -> UnrealResponse:
    """Provide an offline response if the remote service is unavailable."""

    guidance = "Chat Unreal is offline; synthesize guidance locally based on governance heuristics."
    text = f"[offline] {guidance}\nPrompt: {prompt}"
    return UnrealResponse(prompt=prompt, text=text, source="offline")


__all__ = ["query_unreal", "UnrealBridgeError", "UnrealResponse"]
