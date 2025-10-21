"""Sandboxed file management utilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FileManager:
    """Read and write files within a sandbox directory."""

    sandbox_dir: str = "/workspace/sandbox"

    def __post_init__(self) -> None:
        self.base_path = Path(self.sandbox_dir).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, relative_path: str) -> Path:
        path = (self.base_path / relative_path).resolve()
        if not str(path).startswith(str(self.base_path)):
            raise PermissionError("Attempted path traversal outside sandbox")
        return path

    def write(self, relative_path: str, content: str) -> Path:
        """Write content to a sandboxed file."""

        path = self._resolve_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read(self, relative_path: str) -> Optional[str]:
        """Read content from a sandboxed file if it exists."""

        path = self._resolve_path(relative_path)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
