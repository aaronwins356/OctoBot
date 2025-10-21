"""Central logging utilities for OctoBot."""
from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from .utils import ensure_directory, repo_root, timestamp

_LOG_PATH = repo_root() / "memory" / "system.log"
ensure_directory(_LOG_PATH.parent)

_LOGGERS: Dict[str, logging.Logger] = {}


def _serialise_details(details: Any) -> Any:
    if isinstance(details, (str, int, float, bool)) or details is None:
        return details
    if isinstance(details, dict):
        return details
    if isinstance(details, (list, tuple)):
        return list(details)
    return repr(details)


def _configure_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"octobot.{name}")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(_LOG_PATH, maxBytes=1_048_576, backupCount=3)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(agent: str) -> logging.Logger:
    """Return a logger instance scoped to *agent*."""
    if agent not in _LOGGERS:
        _LOGGERS[agent] = _configure_logger(agent)
    return _LOGGERS[agent]


def log_event(agent: str, action: str, status: str, details: Any) -> None:
    """Write a structured log entry."""
    entry = {
        "time": timestamp(),
        "agent": agent,
        "action": action,
        "status": status,
        "details": _serialise_details(details),
    }
    get_logger(agent).info(json.dumps(entry, sort_keys=False))


def capture_exception(agent: str, action: str, error: BaseException) -> None:
    """Record details about an uncaught exception."""
    log_event(
        agent=agent,
        action=action,
        status="error",
        details={"error": repr(error)},
    )
