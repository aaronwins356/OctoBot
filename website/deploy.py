"""Deployment helper for publishing the generated portfolio."""
from __future__ import annotations

from pathlib import Path
from typing import List

from government.presenter import build_portfolio
from utils.logger import get_logger

LOGGER = get_logger(__name__)


def build_only(output_dir: str = "website/public") -> List[Path]:
    """Generate the static site without transferring it anywhere."""

    LOGGER.info("Building site for manual deployment")
    return build_portfolio(Path(output_dir))


__all__ = ["build_only"]
