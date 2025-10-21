"""Command line client for interacting with Chat Unreal."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests

from .auth import load_token

DEFAULT_BASE_URL = "http://127.0.0.1:8080"


def _post(endpoint: str, payload: dict[str, Any], token: str, base_url: str) -> dict[str, Any]:
    response = requests.post(
        f"{base_url}/api/{endpoint}",
        json=payload,
        headers={"X-API-KEY": token, "Content-Type": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chat Unreal command line client")
    parser.add_argument("endpoint", choices=["research", "market", "github"], help="API endpoint to query")
    parser.add_argument("value", help="Query string, topic or keyword depending on endpoint")
    parser.add_argument("--token", dest="token", help="API token (defaults to OCTOBOT_KEY env)")
    parser.add_argument("--base-url", dest="base_url", default=DEFAULT_BASE_URL, help="Base URL of Chat Unreal server")

    args = parser.parse_args(argv)
    token = load_token(args.token)

    payload_key = {"research": "query", "market": "topic", "github": "keyword"}[args.endpoint]
    payload = {payload_key: args.value}

    try:
        data = _post(args.endpoint, payload, token, args.base_url.rstrip("/"))
    except requests.HTTPError as exc:  # pragma: no cover - network failure path
        sys.stderr.write(f"Request failed: {exc}\n")
        return 1

    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
