"""RSS feed reader with caching support."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import feedparser

from .. import config

_CACHE_DIR = config.CACHE_DIR / "rss"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class FeedResult:
    url: str
    fetched_at: float
    entries: list[dict[str, Any]]


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode()).hexdigest()
    return _CACHE_DIR / f"{digest}.json"


def _load_from_cache(url: str) -> FeedResult | None:
    path = _cache_path(url)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > config.CACHE_TTL_SECONDS:
        return None
    with path.open("r", encoding="utf-8") as file:
        raw = json.load(file)
    return FeedResult(**raw)


def _save_to_cache(result: FeedResult) -> None:
    with _cache_path(result.url).open("w", encoding="utf-8") as file:
        json.dump(result.__dict__, file)


def read_feed(url: str) -> dict[str, Any]:
    """Fetch an RSS/Atom feed and return serialized entries."""

    cached = _load_from_cache(url)
    if cached:
        return {
            "url": cached.url,
            "fetched_at": cached.fetched_at,
            "entries": cached.entries,
        }

    parsed = feedparser.parse(url)
    entries = []
    for entry in parsed.entries[:20]:
        entries.append(
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
            }
        )

    result = FeedResult(url=url, fetched_at=time.time(), entries=entries)
    _save_to_cache(result)
    return {
        "url": result.url,
        "fetched_at": result.fetched_at,
        "entries": result.entries,
    }
