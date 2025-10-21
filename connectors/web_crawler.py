"""Documentation crawler leveraging the unreal bridge."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from connectors.unreal_bridge import UnrealBridge
from laws.validator import enforce
from memory.logger import log_event


class DocumentationCrawler:
    def __init__(self, bridge: UnrealBridge | None = None) -> None:
        self.bridge = bridge or UnrealBridge()

    def fetch(self, topic: str) -> Dict[str, str]:
        response = self.bridge.request("/docs", {"topic": topic})
        log_event("crawler", "fetch", "completed", {"topic": topic})
        return response.payload

    def save(self, topic: str, target_dir: Path) -> Path:
        enforce("filesystem_write", str(target_dir))
        target_dir.mkdir(parents=True, exist_ok=True)
        data = self.fetch(topic)
        destination = target_dir / f"{topic.replace(' ', '_')}.txt"
        enforce("filesystem_write", str(destination))
        destination.write_text("\n".join(f"{k}: {v}" for k, v in data.items()), encoding="utf-8")
        log_event("crawler", "save", "completed", destination.as_posix())
        return destination
