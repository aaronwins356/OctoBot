"""In-memory analytics store used to inspire venture ideation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class TrafficMetric:
    """A lightweight representation of a traffic signal."""

    source: str
    visitors: int
    conversion_rate: float


def load_metrics() -> List[TrafficMetric]:
    """Return placeholder metrics until real analytics integrations are approved."""

    return [
        TrafficMetric(source="newsletter", visitors=320, conversion_rate=0.08),
        TrafficMetric(source="organic_search", visitors=780, conversion_rate=0.04),
        TrafficMetric(source="referrals", visitors=150, conversion_rate=0.05),
    ]


__all__ = ["TrafficMetric", "load_metrics"]
