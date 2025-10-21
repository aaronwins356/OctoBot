"""
File: chat_unreal/connectors/api_handler.py
Fix Type: Security / Networking
Summary:
- ✅ Fixed: missing strict domain validation before outbound requests
- ✅ Added: ledger-backed persistence via safe_write
- ✅ Tested by: tests/test_connector_domains.py

All external URLs are validated through :func:`validate_domain` to guarantee
whitelisted hostnames.  The cache store uses :func:`safe_write` to respect the
filesystem laws prior to persisting data.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import requests

from octobot.utils.persistence import safe_write

from .. import config
from ..api.utils import logging_utils
from ..api.utils.validators import ValidationError
from ..validators.domain_validator import validate_domain
from . import rss_reader, web_fetch


@dataclass(slots=True)
class CachedResponse:
    key: str
    data: dict[str, Any]
    stored_at: float


class CacheStore:
    """Safe JSON-based cache for connector responses."""

    def __init__(self, namespace: str) -> None:
        self._path = config.CACHE_DIR / f"{namespace}.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, CachedResponse]:
        if not self._path.exists():
            return {}
        with self._path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
        cache: dict[str, CachedResponse] = {}
        for key, value in raw.items():
            cache[key] = CachedResponse(key=key, data=value["data"], stored_at=value["stored_at"])
        return cache

    def save(self, cache: dict[str, CachedResponse]) -> None:
        serializable = {
            key: {"data": value.data, "stored_at": value.stored_at} for key, value in cache.items()
        }
        safe_write(self._path, json.dumps(serializable, indent=2), category="connector_cache")


@dataclass(slots=True)
class ResearchMemory:
    """Persisted store of previous research queries."""

    path: Path = field(default_factory=lambda: config.RESEARCH_HISTORY_FILE)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def append(self, record: dict[str, Any]) -> None:
        history = self.load()
        history.append(record)
        safe_write(self.path, json.dumps(history[-200:], indent=2), category="research_history")


class APIHandler:
    """Core integration manager for Chat Unreal."""

    def __init__(self) -> None:
        self._cache = CacheStore("api_handler")
        self._memory = ResearchMemory()
        self._session = requests.Session()
        self._local_cache = self._cache.load()

    def research(self, query: str) -> dict[str, Any]:
        key = f"research::{query.lower()}"
        cached = self._local_cache.get(key)
        if cached and time.time() - cached.stored_at < config.CACHE_TTL_SECONDS:
            return cached.data

        sources = ["https://news.ycombinator.com/"]
        rss_sources = ["https://news.ycombinator.com/rss"]
        insights: list[dict[str, Any]] = []
        for source in sources:
            validate_domain(source)
            result = web_fetch.fetch(source)
            if "error" in result:
                continue
            for link in result["metadata"].get("links", []):
                try:
                    validate_domain(link["url"])
                except ValidationError:
                    continue
                title = link["title"].lower()
                if all(token in title for token in query.lower().split()):
                    insights.append(
                        {
                            "title": link["title"],
                            "source": source,
                            "url": link["url"],
                        }
                    )
            if insights:
                break

        if not insights:
            for feed_url in rss_sources:
                validate_domain(feed_url)
                try:
                    feed = rss_reader.read_feed(feed_url)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    logging_utils.LOGGER.warning("RSS fetch failed: %s", exc)
                    continue
                for entry in feed.get("entries", []):
                    link = entry.get("link", "")
                    try:
                        validate_domain(link)
                    except ValidationError:
                        continue
                    title = entry.get("title", "").lower()
                    if all(token in title for token in query.lower().split()):
                        insights.append(
                            {
                                "title": entry.get("title", ""),
                                "source": feed_url,
                                "url": link,
                            }
                        )
                if insights:
                    break

        if not insights:
            insights = self._fallback_insights(query)

        top_insights = insights[:10]
        response = {
            "query": query,
            "generated_at": time.time(),
            "insights": top_insights,
            "sources": sources,
        }

        self._remember_query(query, top_insights)
        self._update_cache(key, response)
        return response

    def _fallback_insights(self, query: str) -> list[dict[str, Any]]:
        keywords = query.split()
        summary = " ".join(keyword.capitalize() for keyword in keywords)
        return [
            {
                "title": f"Trend insight for {summary}",
                "source": "synthetic",
                "url": "",
            }
        ]

    def _remember_query(self, query: str, insights: Iterable[dict[str, Any]]) -> None:
        record = {
            "query": query,
            "timestamp": time.time(),
            "insight_count": sum(1 for _ in insights),
        }
        self._memory.append(record)

    def _update_cache(self, key: str, data: dict[str, Any]) -> None:
        cached = CachedResponse(key=key, data=data, stored_at=time.time())
        self._local_cache[key] = cached
        self._cache.save(self._local_cache)

    def github_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        base = "https://api.github.com"
        validate_domain(base)
        url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}"
        response = self._session.get(url, params=params or {}, timeout=10)
        response.raise_for_status()
        return response.json()

