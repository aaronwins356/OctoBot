"""Bridge to the Chat Unreal internal service."""
from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from laws.validator import enforce
from memory.logger import log_event
from memory.utils import repo_root


@dataclass
class BridgeRequest:
    endpoint: str
    payload: Dict[str, Any]
    attempt: int = 0


@dataclass
class BridgeResponse:
    status: str
    payload: Dict[str, Any]


class UnrealBridge:
    """Queue based connector with retry logic."""

    def __init__(self, service_path: Path | None = None, max_retries: int = 3) -> None:
        self.service_path = service_path or repo_root() / "chat_unreal"
        self.max_retries = max_retries
        self._queue: "queue.Queue[BridgeRequest]" = queue.Queue()
        self._lock = threading.Lock()

    def request(self, endpoint: str, payload: Dict[str, Any]) -> BridgeResponse:
        enforce("external_request", Path(__file__).as_posix())
        self._ensure_service()
        request = BridgeRequest(endpoint=endpoint, payload=payload)
        self._queue.put(request)
        return self._process_queue()

    def _process_queue(self) -> BridgeResponse:
        request = self._queue.get()
        delay = 0.5
        while request.attempt <= self.max_retries:
            try:
                response = self._send(request)
                log_event("unreal_bridge", "request", "success", {"endpoint": request.endpoint})
                return response
            except Exception as error:  # pragma: no cover - defensive logging
                request.attempt += 1
                log_event(
                    "unreal_bridge",
                    "request",
                    "retry",
                    {"endpoint": request.endpoint, "attempt": request.attempt, "error": repr(error)},
                )
                if request.attempt > self.max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
        raise RuntimeError("Request retry loop exhausted")

    def _ensure_service(self) -> None:
        with self._lock:
            if self._health_check():
                return
            self._launch_service()
            timeout = time.time() + 5
            while time.time() < timeout:
                if self._health_check():
                    return
                time.sleep(0.5)
            raise RuntimeError("Chat Unreal service failed health check")

    def _health_check(self) -> bool:
        health_file = self.service_path / "health.json"
        return health_file.exists()

    def _launch_service(self) -> None:
        script = self.service_path / "api" / "server.py"
        if not script.exists():
            raise FileNotFoundError("chat_unreal/api/server.py not found")
        log_event("unreal_bridge", "launch", "pending", script.as_posix())

    def _send(self, request: BridgeRequest) -> BridgeResponse:
        mock_path = self.service_path / "api" / "responses" / f"{request.endpoint.strip('/')}.json"
        if not mock_path.exists():
            raise FileNotFoundError(f"No mock response for {request.endpoint}")
        data = json.loads(mock_path.read_text(encoding="utf-8"))
        payload = {"request": request.payload, "response": data}
        return BridgeResponse(status="ok", payload=payload)


def call_unreal(endpoint: str, payload: Dict[str, Any]) -> BridgeResponse:
    bridge = UnrealBridge()
    return bridge.request(endpoint, payload)
