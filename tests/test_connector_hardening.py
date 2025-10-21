from __future__ import annotations

from typing import Any

import httpx

from octobot.connectors import unreal_bridge


class _FailingClient:
    calls: list[float] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        _FailingClient.calls.append(timeout)

    def __enter__(self) -> "_FailingClient":
        return self

    def __exit__(self, *exc: Any) -> None:  # pragma: no cover - context protocol
        return None

    def post(self, *args: Any, **kwargs: Any) -> httpx.Response:
        raise httpx.TimeoutException("simulated timeout")


def test_unreal_bridge_retries_and_falls_back(monkeypatch) -> None:
    _FailingClient.calls.clear()

    def fake_client(timeout: float) -> _FailingClient:
        return _FailingClient(timeout)

    fake_httpx = type(
        "FakeHttpx",
        (),
        {
            "Client": fake_client,
            "HTTPError": httpx.HTTPError,
            "TimeoutException": httpx.TimeoutException,
        },
    )
    monkeypatch.setattr(unreal_bridge, "httpx", fake_httpx)

    response = unreal_bridge.query_unreal("hello")
    assert response.startswith("[offline]")
    assert len(_FailingClient.calls) == unreal_bridge._MAX_RETRIES + 1
    assert all(timeout == unreal_bridge._TIMEOUT for timeout in _FailingClient.calls)
