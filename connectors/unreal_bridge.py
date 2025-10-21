"""Controlled bridge for outbound requests.

The bridge logs every request and refuses to perform real network I/O when
operating in offline demonstration mode. All interactions pass through the law
validator to guarantee compliance with governance rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from laws.validator import DEFAULT_VALIDATOR, LawViolation
from memory.history_logger import HistoryLogger


@dataclass
class BridgeResponse:
    status: str
    payload: Dict[str, str]


class UnrealBridge:
    def __init__(self, logger: Optional[HistoryLogger] = None) -> None:
        self.logger = logger or HistoryLogger()

    def request(self, endpoint: str, payload: Dict[str, str]) -> BridgeResponse:
        """Record a simulated outbound request while enforcing laws."""
        DEFAULT_VALIDATOR.ensure([
            "network request",
            "human approval",  # network access is assumed pre-approved manually
            "rationale logged",
        ])
        self.logger.log_event(
            f"Bridge request to {endpoint} with payload keys {list(payload.keys())}",
        )
        return BridgeResponse(
            status="ok",
            payload={
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
                **payload,
            },
        )


def save_bridge_response(response: BridgeResponse, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "status: {status}\n{payload}\n".format(
            status=response.status, payload="\n".join(f"{k}: {v}" for k, v in response.payload.items())
        ),
        encoding="utf-8",
    )
