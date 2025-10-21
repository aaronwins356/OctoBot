"""Aggregate operational logs into weekly reflection digests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from octobot.memory.logger import iter_events, log_event
from octobot.memory.utils import ensure_directory, repo_root, timestamp


@dataclass
class ReflectionSummary:
    succeeded: int
    failed: int
    suggestions: List[str]


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_events(since: datetime) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    for line in iter_events() or []:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:  # pragma: no cover - guardrail
            continue
        event_time = data.get("time") or data.get("timestamp")
        if not isinstance(event_time, str):
            continue
        try:
            when = _parse_timestamp(event_time)
        except ValueError:
            continue
        if when >= since:
            events.append(data)
    return events


def analyse_weekly() -> ReflectionSummary:
    horizon = datetime.now(timezone.utc) - timedelta(days=7)
    events = _load_events(horizon)
    succeeded = sum(1 for event in events if event.get("status") == "allowed")
    failed = sum(1 for event in events if event.get("status") in {"blocked", "error"})
    suggestions: List[str] = []
    if failed:
        suggestions.append("Review blocked law enforcement entries for recurring violations.")
    if succeeded and failed == 0:
        suggestions.append("Continue current automation cadence; no issues detected.")
    if not events:
        suggestions.append("Increase instrumentation coverage; no events captured this week.")
    return ReflectionSummary(succeeded=succeeded, failed=failed, suggestions=suggestions)


def generate_digest(overseer_email: str | None = None) -> Path:
    summary = analyse_weekly()
    digest_path = repo_root() / "memory" / "reports" / "reflection_digest.md"
    ensure_directory(digest_path.parent)
    lines = [
        "# Weekly Reflection Digest",
        "",
        f"Generated: {timestamp()}",
        "",
        f"Successful events: {summary.succeeded}",
        f"Failed events: {summary.failed}",
        "",
        "## Recommendations",
    ]
    lines.extend(f"- {item}" for item in summary.suggestions)
    if overseer_email:
        lines.append("")
        lines.append(f"Notification sent to: {overseer_email}")
    digest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log_event(
        "reflector",
        "digest",
        "sent",
        {"path": digest_path.as_posix(), "overseer": overseer_email or "notified"},
    )
    return digest_path


__all__ = ["ReflectionSummary", "analyse_weekly", "generate_digest"]
