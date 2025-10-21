"""Logging utilities for the Chat Unreal API."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ... import config


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger("chat_unreal.api")
    if not logger.handlers:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(config.LOG_FILE)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


LOGGER = _configure_logger()


def log_api_call(endpoint: str, payload: dict[str, Any] | None) -> None:
    """Log API calls with endpoint and payload metadata."""

    payload_size = len(json.dumps(payload or {}))
    LOGGER.info("endpoint=%s payload_size=%d", endpoint, payload_size)


def log_to_file(path: Path, data: dict[str, Any]) -> None:
    """Append structured JSON data to the specified log file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), **data}
        file.write(json.dumps(record) + "\n")
