"""Safe HTTP fetching utilities with caching and robots.txt compliance."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from .. import config
from ..api.utils import validators
from octobot.connectors.utils import ensure_safe_content, log_connector_call, sanitize_text

_USER_AGENT = "ChatUnrealBot/1.0 (+https://example.com/contact)"
_CACHE_DIR = config.CACHE_DIR / "web"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_ROBOT_CACHE: dict[str, RobotFileParser] = {}
_MAX_RETRIES = 2


@dataclass(slots=True)
class FetchResult:
    url: str
    fetched_at: float
    status_code: int
    content: str
    metadata: dict[str, Any]


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode()).hexdigest()
    return _CACHE_DIR / f"{digest}.json"


def _load_from_cache(url: str) -> FetchResult | None:
    path = _cache_path(url)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > config.CACHE_TTL_SECONDS:
        return None
    with path.open("r", encoding="utf-8") as file:
        raw = json.load(file)
    return FetchResult(**raw)


def _save_to_cache(result: FetchResult) -> None:
    path = _cache_path(result.url)
    with path.open("w", encoding="utf-8") as file:
        json.dump(result.__dict__, file)


def _http_get(url: str, *, headers: dict[str, str]) -> httpx.Response:
    last_error: BaseException | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = httpx.get(url, headers=headers, timeout=config.DEFAULT_TIMEOUT)
            ensure_safe_content(response.headers.get("Content-Type", "text/plain"))
            log_connector_call(
                "chat_unreal.web_fetch",
                url,
                "success",
                {"status_code": response.status_code, "attempt": attempt},
            )
            return response
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            log_connector_call(
                "chat_unreal.web_fetch",
                url,
                "error",
                {"attempt": attempt, "error": repr(exc)},
            )
    raise RuntimeError(f"Failed to fetch {url}: {last_error!r}")


def _robots_for(url: str) -> RobotFileParser:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robot_url = f"{base}/robots.txt"
    if base not in _ROBOT_CACHE:
        parser = RobotFileParser()
        try:
            response = _http_get(robot_url, headers={"User-Agent": _USER_AGENT})
            if response.status_code == 200:
                parser.parse(sanitize_text(response.text).splitlines())
            else:
                parser = RobotFileParser()
                parser.parse(["User-agent: *", "Disallow:"])
        except Exception:
            parser = RobotFileParser()
            parser.parse(["User-agent: *", "Disallow:"])
        _ROBOT_CACHE[base] = parser
    return _ROBOT_CACHE[base]


def is_allowed(url: str) -> bool:
    validators.validate_domain(url)
    parser = _robots_for(url)
    return parser.can_fetch(_USER_AGENT, url)


def fetch(url: str, *, force_refresh: bool = False) -> dict[str, Any]:
    """Fetch a URL if allowed and return parsed metadata."""

    if not is_allowed(url):
        return {"error": "Disallowed by robots.txt", "url": url}

    if not force_refresh:
        cached = _load_from_cache(url)
        if cached:
            return {
                "url": cached.url,
                "fetched_at": cached.fetched_at,
                "status_code": cached.status_code,
                "metadata": cached.metadata,
            }

    try:
        response = _http_get(url, headers={"User-Agent": _USER_AGENT})
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network failure path
        return {"error": str(exc), "url": url}

    soup = BeautifulSoup(sanitize_text(response.text), "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = (
        description_tag["content"].strip()
        if description_tag and description_tag.get("content")
        else ""
    )
    links: list[dict[str, str]] = []
    for anchor in soup.select("a[href]")[:20]:
        href = anchor.get("href", "").strip()
        text = anchor.get_text(strip=True)
        if href and text:
            links.append({"title": text, "url": href})

    metadata = {
        "title": title,
        "description": description,
        "links": links,
    }

    result = FetchResult(
        url=url,
        fetched_at=time.time(),
        status_code=response.status_code,
        content=response.text,
        metadata=metadata,
    )
    _save_to_cache(result)
    return {
        "url": result.url,
        "fetched_at": result.fetched_at,
        "status_code": result.status_code,
        "metadata": result.metadata,
    }
