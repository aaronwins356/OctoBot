"""Documentation crawler leveraging the Chat Unreal bridge."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from octobot.connectors.unreal_bridge import query_unreal
from octobot.laws.validator import enforce
from octobot.memory.logger import log_event


class DocumentationCrawler:
    """Fetch lightweight documentation guidance from Chat Unreal."""

    def fetch(self, topic: str) -> Dict[str, str]:
        prompt = f"Provide a concise documentation outline for {topic}."
        summary = query_unreal(prompt)
        log_event("crawler", "fetch", "completed", {"topic": topic})
        return {"topic": topic, "summary": summary}

    def save(self, topic: str, target_dir: Path) -> Path:
        enforce("filesystem_write", str(target_dir))
        target_dir.mkdir(parents=True, exist_ok=True)
        data = self.fetch(topic)
        destination = target_dir / f"{topic.replace(' ', '_')}.txt"
        enforce("filesystem_write", str(destination))
        content = f"Topic: {data['topic']}\n\n{data['summary']}\n"
        destination.write_text(content, encoding="utf-8")
        log_event("crawler", "save", "completed", destination.as_posix())
        return destination


class WebCrawler:
    """Generic wrapper for sanctioned web lookups via Unreal bridge."""

    def search(self, topic: str, limit: int = 5) -> List[str]:
        prompt = f"Summarise recent public info about {topic}."
        response = query_unreal(prompt)
        log_event(
            "crawler",
            "search",
            "completed",
            {"topic": topic, "limit": limit},
        )
        return [response][:limit]


__all__ = ["DocumentationCrawler", "WebCrawler"]
