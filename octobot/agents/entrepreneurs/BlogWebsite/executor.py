"""Blog website simulation executor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from octobot.connectors.web_crawler import WebCrawler
from octobot.laws.validator import enforce, guard, register_agent
from octobot.memory.logger import log_event

register_agent("entrepreneur.blog")


@dataclass
class ArticleDraft:
    title: str
    summary: str
    sources: List[str]


class BlogExecutor:
    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path("proposals/blog")
        self.crawler = WebCrawler()

    @guard("entrepreneur.blog")
    def draft(self, topic: str) -> ArticleDraft:
        enforce("filesystem_write", str(self.output_dir))
        documents = self.crawler.search(topic, limit=2)
        summary = f"Exploring {topic} through constitutional AI practices."
        draft = ArticleDraft(title=topic.title(), summary=summary, sources=documents)
        log_event(
            "entrepreneur.blog",
            "draft",
            "completed",
            {"topic": topic, "sources": len(documents)},
        )
        return draft


__all__ = ["BlogExecutor", "ArticleDraft"]
