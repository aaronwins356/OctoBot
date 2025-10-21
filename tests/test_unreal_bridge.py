from __future__ import annotations

import json
from pathlib import Path

import pytest

from connectors.unreal_bridge import UnrealBridge


def _prepare_service(tmp_path: Path) -> Path:
    health = tmp_path / "health.json"
    health.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
    responses = tmp_path / "api" / "responses"
    responses.mkdir(parents=True, exist_ok=True)
    responses.joinpath("ping.json").write_text(json.dumps({"message": "pong"}), encoding="utf-8")
    return tmp_path


def test_unreal_bridge_success(tmp_path: Path) -> None:
    service = _prepare_service(tmp_path)
    bridge = UnrealBridge(service_path=service)
    response = bridge.request("/ping", {"value": 1})
    assert response.status == "ok"
    assert response.payload["response"]["message"] == "pong"


def test_unreal_bridge_missing_response(tmp_path: Path) -> None:
    service = _prepare_service(tmp_path)
    bridge = UnrealBridge(service_path=service)
    with pytest.raises(FileNotFoundError):
        bridge.request("/unknown", {})
