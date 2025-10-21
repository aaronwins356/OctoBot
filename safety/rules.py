"""Safety rules enforcing guardrails across the system."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class SafetyRules:
    """Simple safety filters for textual commands."""

    blocked_phrases: Iterable[str] = ("delete system32", "rm -rf /")

    def is_task_allowed(self, description: str) -> bool:
        """Return True when the task description passes the safety filter."""

        lowered = description.lower()
        return all(phrase not in lowered for phrase in self.blocked_phrases)

    def check_response(self, response: str) -> bool:
        """Validate generated responses using the same blocked phrase check."""

        return self.is_task_allowed(response)
