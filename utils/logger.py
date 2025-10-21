"""Central logging utilities for the AI Republic project.

The `get_logger` helper returns configured loggers that write to rotating log
files under the path defined in the global configuration. All modules must use
this helper to ensure consistent formatting and tamper-evident output.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict

from utils.settings import SETTINGS

_LOGGERS: Dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Return a module-specific logger configured with rotation.

    Loggers are cached to avoid duplicate handlers. Logs are written to
    `<logs_dir>/ai_republic.log` by default with a 1 MB rotation.
    """

    if name in _LOGGERS:
        return _LOGGERS[name]

    logs_dir = Path(SETTINGS.runtime.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "ai_republic.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(logging.StreamHandler())

    logger.propagate = False
    _LOGGERS[name] = logger
    return logger
