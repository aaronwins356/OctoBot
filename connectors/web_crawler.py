"""Documentation crawler leveraging the unreal bridge."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from connectors.unreal_bridge import UnrealBridge
from memory.history_logger import HistoryLogger


class DocumentationCrawler:
    def __init__(self, bridge: UnrealBridge | None = None, logger: HistoryLogger | None = None) -> None:
        self.logger = logger or HistoryLogger()
        self.bridge = bridge or UnrealBridge(self.logger)

    def fetch(self, topic: str) -> Dict[str, str]:
        response = self.bridge.request("/docs", {"topic": topic})
        self.logger.log_event(f"Documentation fetched for topic '{topic}'")
        return response.payload

    def save(self, topic: str, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        data = self.fetch(topic)
        destination = target_dir / f"{topic.replace(' ', '_')}.txt"
        destination.write_text("\n".join(f"{k}: {v}" for k, v in data.items()), encoding="utf-8")
        self.logger.log_event(f"Documentation saved to {destination}")
        return destination
