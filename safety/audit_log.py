"""Audit logging for all orchestrator operations."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def _default_log_path() -> Path:
    log_dir = Path(os.environ.get("LOG_DIR", "/workspace/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "audit.log"


@dataclass
class AuditLogger:
    """Structured logger that appends JSON events to the audit log."""

    log_path: Path = _default_log_path()

    def __post_init__(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO)

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Append a structured event to the audit log."""

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "payload": payload,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
