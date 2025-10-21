"""Marketing advisory component for venture planning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class MarketingIdea:
    """Simple representation of an outreach or SEO concept."""

    channel: str
    narrative: str


class MarketerAgent:
    """Suggests ethical marketing experiments for proposed ventures."""

    name: str = "marketer_agent"

    def seo_playbook(self, focus_keyword: str) -> List[MarketingIdea]:
        """Return gentle SEO tactics that require human approval before execution."""

        return [
            MarketingIdea(
                channel="Blog Editorial Calendar",
                narrative=(
                    f"Draft a three-part series expanding on {focus_keyword} with evidence-backed research "
                    "and human-edited storytelling."
                ),
            ),
            MarketingIdea(
                channel="Newsletter",
                narrative="Invite subscribers to a monthly digest highlighting experiment outcomes and wellness tips.",
            ),
            MarketingIdea(
                channel="Partnership Outreach",
                narrative=(
                    "Identify two wellness podcasters whose audiences align with our mission and propose mutually "
                    "beneficial collaborations."
                ),
            ),
        ]


__all__ = ["MarketerAgent", "MarketingIdea"]
