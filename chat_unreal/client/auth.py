"""Client-side authentication utilities."""

from __future__ import annotations

import os
from typing import Optional


def load_token(explicit: Optional[str] = None) -> str:
    """Load the API token from parameter or environment."""

    token = explicit or os.getenv("OCTOBOT_KEY")
    if not token:
        raise RuntimeError("OCTOBOT_KEY must be provided via argument or environment")
    return token
