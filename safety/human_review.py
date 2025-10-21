"""Human review checkpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class HumanReviewGate:
    """Require an explicit approval callback before executing actions."""

    approval_callback: Callable[[str], bool]

    def require_approval(self, description: str) -> bool:
        """Invoke the approval callback and return the result."""

        return bool(self.approval_callback(description))
