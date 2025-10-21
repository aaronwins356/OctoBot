"""Compatibility wrapper around the Flask dashboard."""
from __future__ import annotations

from website.app import create_app

__all__ = ["create_app"]
