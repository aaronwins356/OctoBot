"""
File: octobot/utils/persistence.py
Fix Type: Security / Filesystem
Summary:
- ✅ Fixed: missing constitutional enforcement on file writes
- ✅ Added: safe_write helper routing writes through laws.enforcer
- ✅ Tested by: tests/test_persistence_enforcement.py

All modules must now write through :func:`safe_write`, guaranteeing that the
law enforcer is consulted before touching the filesystem.  The helper logs the
operation in a transparent ledger entry to preserve auditability.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from octobot.laws import enforcer
from octobot.memory.logger import log_event

LOGGER = logging.getLogger(__name__)

PathLike = Union[str, Path]


def safe_write(path: PathLike, data: str, *, category: str = "general") -> None:
    """Write *data* to *path* after passing constitutional checks."""

    target = Path(path)
    enforcer.enforce("filesystem_write", str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        handle.write(data)
    log_event(
        "filesystem",
        "write",
        "allowed",
        {"path": str(target), "category": category, "size": len(data)},
    )
    LOGGER.debug("safe_write persisted %s (%s bytes)", target, len(data))

