"""Structlog-backed logging utilities for OctoBot."""

from __future__ import annotations

from typing import Any, cast

import structlog

from octobot.memory.utils import ensure_directory, log_file_path, timestamp

_EVENT_LOG = log_file_path()
ensure_directory(_EVENT_LOG.parent)


def _configure_structlog() -> None:
    if structlog.is_configured():  # pragma: no cover - defensive
        return
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.WriteLoggerFactory(
            file=_EVENT_LOG.open("a", encoding="utf-8")
        ),
    )


_configure_structlog()


def _serialise_details(details: Any) -> Any:
    if isinstance(details, (str, int, float, bool)) or details is None:
        return details
    if isinstance(details, dict):
        return details
    if isinstance(details, (list, tuple, set)):
        return list(details)
    return repr(details)


def get_logger(agent: str) -> structlog.BoundLogger:
    """Return a structlog logger bound to *agent*."""

    return cast(structlog.BoundLogger, structlog.get_logger(agent=agent))


def log_event(agent: str, action: str, status: str, details: Any) -> None:
    """Write an immutable JSON log entry for an action."""

    logger = get_logger(agent)
    logger.info(
        "event",
        action=action,
        status=status,
        time=timestamp(),
        details=_serialise_details(details),
    )


def capture_exception(agent: str, action: str, error: BaseException) -> None:
    """Record exception metadata in the telemetry stream."""

    log_event(agent, action, "error", {"error": repr(error)})


def iter_events() -> Any:
    """Yield raw log entries from the event log."""

    if not _EVENT_LOG.exists():
        return
    with _EVENT_LOG.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield line


__all__ = ["log_event", "capture_exception", "get_logger", "iter_events"]
