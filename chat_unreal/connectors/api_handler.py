"""High-level API integrations used by Chat Unreal routes."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import requests

from .. import config
from ..api.utils import logging_utils, validators
from . import rss_reader, web_fetch


@dataclass(slots=True)
class CachedResponse:
    key: str
    data: dict[str, Any]
    stored_at: float


class CacheStore:
    """Simple JSON-based cache for connector responses."""

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
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(serializable, file, indent=2)


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
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(history[-200:], file, indent=2)


class APIHandler:
    """Core integration manager for Chat Unreal."""

    def __init__(self) -> None:
        self._cache = CacheStore("api_handler")
        self._memory = ResearchMemory()
        self._session = requests.Session()
        self._local_cache = self._cache.load()

    # ------------------------------------------------------------------
    # Research
    def research(self, query: str) -> dict[str, Any]:
        key = f"research::{query.lower()}"
        cached = self._local_cache.get(key)
        if cached and time.time() - cached.stored_at < config.CACHE_TTL_SECONDS:
            return cached.data

        sources = ["https://news.ycombinator.com/"]
        rss_sources = ["https://news.ycombinator.com/rss"]
        insights: list[dict[str, Any]] = []
        for source in sources:
            validators.validate_domain(source)
            result = web_fetch.fetch(source)
            if "error" in result:
                continue
            for link in result["metadata"].get("links", []):
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
                validators.validate_domain(feed_url)
                try:
                    feed = rss_reader.read_feed(feed_url)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    logging_utils.LOGGER.warning("RSS fetch failed: %s", exc)
                    continue
                for entry in feed.get("entries", []):
                    title = entry.get("title", "").lower()
                    if all(token in title for token in query.lower().split()):
                        insights.append(
                            {
                                "title": entry.get("title", ""),
                                "source": feed_url,
                                "url": entry.get("link", ""),
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

    # ------------------------------------------------------------------
    # Market analysis
    def market_analysis(self, topic: str) -> dict[str, Any]:
        key = f"market::{topic.lower()}"
        cached = self._local_cache.get(key)
        if cached and time.time() - cached.stored_at < config.CACHE_TTL_SECONDS:
            return cached.data

        keywords = topic.lower().split()
        sentiment = self._simulate_sentiment(keywords)
        momentum = self._simulate_momentum(keywords)
        response = {
            "topic": topic,
            "generated_at": time.time(),
            "sentiment_score": sentiment,
            "momentum": momentum,
            "highlights": self._market_highlights(topic, sentiment, momentum),
        }
        self._update_cache(key, response)
        return response

    def _simulate_sentiment(self, keywords: list[str]) -> float:
        base = sum(len(keyword) for keyword in keywords) or 1
        return round(min(1.0, max(-1.0, (base % 10 - 5) / 5)), 2)

    def _simulate_momentum(self, keywords: list[str]) -> str:
        score = sum(ord(c) for word in keywords for c in word) % 3
        return ["declining", "stable", "rising"][score]

    def _market_highlights(self, topic: str, sentiment: float, momentum: str) -> list[str]:
        return [
            f"Topic '{topic}' currently shows {momentum} momentum with sentiment {sentiment}.",
            "Monitor news sources for sudden volatility.",
            "Review historical data before making strategic decisions.",
        ]

    # ------------------------------------------------------------------
    # GitHub
    def github_trending(self, keyword: str) -> dict[str, Any]:
        key = f"github::{keyword.lower()}"
        cached = self._local_cache.get(key)
        if cached and time.time() - cached.stored_at < config.CACHE_TTL_SECONDS:
            return cached.data

        url = "https://api.github.com/search/repositories"
        params = {"q": keyword, "sort": "stars", "order": "desc", "per_page": 5}
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "ChatUnrealBot"}
        try:
            response = self._session.get(
                url, params=params, headers=headers, timeout=config.DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            repositories = [
                {
                    "name": item.get("full_name", ""),
                    "url": item.get("html_url", ""),
                    "description": item.get("description", ""),
                    "stars": item.get("stargazers_count", 0),
                }
                for item in data.get("items", [])
            ]
        except requests.RequestException as exc:  # pragma: no cover - network failure path
            logging_utils.LOGGER.warning("GitHub fetch failed: %s", exc)
            repositories = self._fallback_repositories(keyword)

        response = {
            "keyword": keyword,
            "generated_at": time.time(),
            "repositories": repositories,
        }
        self._update_cache(key, response)
        return response

    def _fallback_repositories(self, keyword: str) -> list[dict[str, Any]]:
        return [
            {
                "name": f"sample/{keyword}-starter",
                "url": "https://github.com/example/sample",
                "description": f"Offline fallback data for {keyword}.",
                "stars": 0,
            }
        ]


_HANDLER: APIHandler | None = None


def get_handler() -> APIHandler:
    global _HANDLER
    if _HANDLER is None:
        _HANDLER = APIHandler()
    return _HANDLER
