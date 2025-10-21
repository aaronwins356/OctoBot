from __future__ import annotations

import json
from urllib import error

import pytest

from octobot.connectors.unreal_bridge import query_unreal


class DummyResponse:
    def __init__(self, payload: dict[str, str]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "DummyResponse":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


def test_query_unreal_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"response": "refined answer"}

    def fake_urlopen(request: object, timeout: float) -> DummyResponse:
        return DummyResponse(payload)

    monkeypatch.setattr("octobot.connectors.unreal_bridge.request.urlopen", fake_urlopen)
    result = query_unreal("Describe the repo")
    assert result == "refined answer"


def test_query_unreal_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_error(request: object, timeout: float) -> None:
        raise error.URLError("offline")

    monkeypatch.setattr("octobot.connectors.unreal_bridge.request.urlopen", raise_error)
    result = query_unreal("Hello")
    assert result.startswith("[offline]")
