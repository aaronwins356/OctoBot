"""OctoBot constitutional architecture package."""

from __future__ import annotations

from importlib import metadata

__all__ = ["__version__"]


def __version__() -> str:
    """Return the installed package version."""
    try:
        return metadata.version("self-coding-bot")
    except metadata.PackageNotFoundError:  # pragma: no cover - during development
        return "0.0.0"
