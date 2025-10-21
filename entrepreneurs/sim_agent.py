"""Agent that runs a local simulation returning numeric metrics."""
from __future__ import annotations

import random
from typing import Any, Dict

from entrepreneurs.base_agent import BaseAgent
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class SimAgent(BaseAgent):
    """Returns deterministic pseudo-random metrics to emulate experimentation."""

    def setup(self) -> None:
        random.seed(42)
        LOGGER.info("%s simulation seeded", self.name)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        LOGGER.info("%s running simulation", self.name)
        metrics = {
            "success_rate": round(random.uniform(0.4, 0.9), 2),
            "iterations": random.randint(5, 10),
        }
        return {"metrics": metrics}

    def report(self) -> Dict[str, Any]:
        return {"status": "simulated"}


__all__ = ["SimAgent"]
