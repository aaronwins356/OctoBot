"""Environment validation script."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

REQUIRED_VARS = {
    "APP_ENV": "development",
    "UNREAL_API_URL": "http://127.0.0.1:8080",
    "DB_PATH": "memory/memory.db",
    "AUTO_ANALYZE_INTERVAL": "weekly",
}


def validate_env(custom: Dict[str, str] | None = None) -> Dict[str, str]:
    """Ensure required environment variables are present."""
    env = dict(REQUIRED_VARS)
    env.update(custom or {})
    for key, default in REQUIRED_VARS.items():
        value = os.getenv(key, default)
        if not value:
            raise RuntimeError(f"Missing environment variable: {key}")
        env[key] = value
    db_path = Path(env["DB_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return env


if __name__ == "__main__":  # pragma: no cover
    validated = validate_env()
    for key, value in validated.items():
        print(f"{key}={value}")
