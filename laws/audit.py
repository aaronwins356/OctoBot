"""Audit log helpers providing tamper-evident records."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4096), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_record(record: Dict[str, str]) -> str:
    digest = hashlib.sha256()
    payload = json.dumps(record, sort_keys=True).encode("utf-8")
    digest.update(payload)
    return digest.hexdigest()


def log_event(agent_name: str, action: str, agent_path: Path, result_hash: str) -> Dict[str, str]:
    """Write a tamper-evident audit log entry and return the record."""

    logs_dir = Path(SETTINGS.runtime.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "audit.log.jsonl"

    record = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "agent": agent_name,
        "action": action,
        "agent_sha256": _hash_file(agent_path),
        "result_sha256": result_hash,
        "enforcement_version": SETTINGS.runtime.enforcement_version,
    }
    record["entry_sha256"] = _hash_record(record)

    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")

    LOGGER.info("Audit log entry: %s", record)
    return record


def tail_log(limit: int = 20) -> list[Dict[str, str]]:
    """Return the latest `limit` audit entries for inspection."""

    log_path = Path(SETTINGS.runtime.logs_dir) / "audit.log.jsonl"
    if not log_path.exists():
        return []
    with log_path.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()[-limit:]
    return [json.loads(line) for line in lines]


__all__ = ["log_event", "tail_log"]
