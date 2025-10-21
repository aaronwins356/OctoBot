"""Execute commands inside a restricted sandbox."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class SandboxRunner:
    """Run a restricted set of shell commands."""

    allowed_commands: Iterable[str] = ("pytest", "python")

    def run(self, command: List[str], cwd: str | None = None) -> subprocess.CompletedProcess:
        """Run an allowed command and capture output."""

        if not command:
            raise ValueError("Command must not be empty")
        if command[0] not in self.allowed_commands:
            raise PermissionError(f"Command '{command[0]}' is not permitted")
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
