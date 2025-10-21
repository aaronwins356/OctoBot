from __future__ import annotations

import os
from typing import Any

import pytest

from chat_unreal.api.server import create_app
from chat_unreal.api.utils import validators
from chat_unreal.connectors import api_handler


class DummyHandler:
    def research(self, query: str) -> dict[str, Any]:
        return {"query": query, "generated_at": 0.0, "insights": [], "sources": []}

    def market_analysis(self, topic: str) -> dict[str, Any]:
        return {"topic": topic, "generated_at": 0.0, "sentiment_score": 0.5, "momentum": "stable", "highlights": []}

    def github_trending(self, keyword: str) -> dict[str, Any]:
        return {"keyword": keyword, "generated_at": 0.0, "repositories": []}


@pytest.fixture(autouse=True)
def configure_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCTOBOT_KEY", "test-token")
    monkeypatch.setattr(api_handler, "_HANDLER", DummyHandler())


@pytest.fixture()
def client():
    app = create_app()
    with app.test_client() as client:
        yield client


def test_health_endpoint_returns_ok(client) -> None:
    response = client.get("/api/health/")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"


def test_research_requires_token(client) -> None:
    response = client.post("/api/research/", json={"query": "ai"})
    assert response.status_code == 401


def test_research_returns_data(client) -> None:
    response = client.post(
        "/api/research/",
        json={"query": "ai"},
        headers={"X-API-KEY": "test-token"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["query"] == "ai"


def test_market_returns_data(client) -> None:
    response = client.post(
        "/api/market/",
        json={"topic": "blockchain"},
        headers={"X-API-KEY": "test-token"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["topic"] == "blockchain"


def test_github_returns_data(client) -> None:
    response = client.post(
        "/api/github/",
        json={"keyword": "python"},
        headers={"X-API-KEY": "test-token"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["keyword"] == "python"


def test_validate_payload_missing_field() -> None:
    with pytest.raises(validators.ValidationError):
        validators.validate_payload({}, required_fields=["query"])


def test_validate_domain_allows_whitelisted() -> None:
    validators.validate_domain("https://github.com/openai")
