"""Base class for all entrepreneurs operating within AI Republic."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel

from utils.logger import get_logger

LOGGER = get_logger(__name__)


class AgentReport(BaseModel):
    data: Dict[str, Any]


class BaseAgent:
    """Abstract base class for entrepreneurs."""

    def __init__(self, name: str, sandbox_path: str):
        self.name = name
        self.sandbox_path = Path(sandbox_path)
        self.sandbox_path.mkdir(parents=True, exist_ok=True)
        LOGGER.debug("Initialised agent %s with sandbox %s", name, sandbox_path)

    def setup(self) -> None:
        raise NotImplementedError

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def report(self) -> Dict[str, Any]:
        raise NotImplementedError


__all__ = ["BaseAgent"]
