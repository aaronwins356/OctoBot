"""Minimal YAML helper with optional PyYAML support."""
from __future__ import annotations

from typing import Any, Dict, Iterable

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore


def safe_load(text: str) -> Any:
    if yaml is not None:
        return yaml.safe_load(text)
    return _simple_load(text)


def safe_dump(data: Any, sort_keys: bool = False) -> str:
    if yaml is not None:
        return yaml.safe_dump(data, sort_keys=sort_keys)
    return _simple_dump(data, sort_keys=sort_keys)


def _simple_load(text: str) -> Any:
    result: Dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-") and current_key:
            value = line[1:].strip()
            result.setdefault(current_key, []).append(_strip_quotes(value))
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = _strip_quotes(value)
                current_key = None
            else:
                result[key] = []
                current_key = key
    return result


def _strip_quotes(value: str) -> str:
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    return value


def _simple_dump(data: Any, sort_keys: bool = False) -> str:
    if not isinstance(data, dict):
        raise TypeError("simple YAML dump only supports dictionaries")
    keys = sorted(data.keys()) if sort_keys else data.keys()
    lines: list[str] = []
    for key in keys:
        value = data[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"
