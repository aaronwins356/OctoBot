"""Thin REST connector for the Chat Unreal reasoning service."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib import error, request

from octobot.laws.validator import enforce
from octobot.memory.logger import log_event

DEFAULT_URL = os.environ.get("OCTOBOT_UNREAL_URL", "http://127.0.0.1:8800/query")
_TIMEOUT = float(os.environ.get("OCTOBOT_UNREAL_TIMEOUT", "5.0"))


class UnrealBridgeError(RuntimeError):
    """Raised when the Chat Unreal service cannot be reached."""


@dataclass(frozen=True)
class UnrealResponse:
    """Normalized response payload returned from Chat Unreal."""

    prompt: str
    text: str
    source: str


def query_unreal(prompt: str) -> str:
    """Send *prompt* to the Chat Unreal service and return the response text."""

    enforce("external_request", __file__)
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    request_obj = request.Request(
        DEFAULT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(request_obj, timeout=_TIMEOUT) as response:
            body = response.read().decode("utf-8")
    except error.URLError as exc:
        log_event("unreal_bridge", "query", "offline", {"error": repr(exc)})
        return _fallback(prompt).text

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        log_event("unreal_bridge", "query", "decode_error", {"body": body[:200]})
        return _fallback(prompt).text

    text = str(data.get("response") or data.get("message") or "")
    if not text:
        log_event("unreal_bridge", "query", "empty", {})
        return _fallback(prompt).text

    log_event("unreal_bridge", "query", "ok", {"length": len(text)})
    return text


def _fallback(prompt: str) -> UnrealResponse:
    """Provide an offline response if the remote service is unavailable."""

    guidance = (
        "Chat Unreal is offline; synthesize guidance locally based on governance heuristics."
    )
    text = f"[offline] {guidance}\nPrompt: {prompt}"
    return UnrealResponse(prompt=prompt, text=text, source="offline")


__all__ = ["query_unreal", "UnrealBridgeError", "UnrealResponse"]
