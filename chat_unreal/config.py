"""Configuration helpers for the Chat Unreal service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

BASE_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = BASE_DIR / "data"
CACHE_DIR: Final[Path] = DATA_DIR / "cache"
LOG_DIR: Final[Path] = Path("logs")
LOG_FILE: Final[Path] = LOG_DIR / "api_calls.log"
RESEARCH_HISTORY_FILE: Final[Path] = CACHE_DIR / "research_history.json"
DEFAULT_TIMEOUT: Final[int] = 10
CACHE_TTL_SECONDS: Final[int] = 60 * 30  # 30 minutes

ALLOWED_DOMAINS: Final[tuple[str, ...]] = (
    "github.com",
    "api.github.com",
    "arxiv.org",
    "news.ycombinator.com",
)

DEFAULT_ALLOWED_ENDPOINTS: Final[frozenset[str]] = frozenset(
    {"research", "market", "github", "health"}
)


def ensure_directories() -> None:
    """Ensure that directories used by the service exist."""

    for directory in (DATA_DIR, CACHE_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


ensure_directories()


def get_env_variable(name: str, default: str | None = None) -> str | None:
    """Retrieve an environment variable with optional default."""

    return os.getenv(name, default)
