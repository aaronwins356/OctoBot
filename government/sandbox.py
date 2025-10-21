"""Sandbox management utilities ensuring path isolation and container simulation."""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from laws.enforcement import verify_agent_permissions
from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


@dataclass
class SandboxPaths:
    agent_name: str
    root: Path

    @classmethod
    def create(cls, agent_name: str) -> "SandboxPaths":
        root = Path(SETTINGS.runtime.sandbox_root) / agent_name
        root.mkdir(parents=True, exist_ok=True)
        return cls(agent_name=agent_name, root=root)

    def ensure_within(self, target: Path) -> None:
        verify_agent_permissions(target)


def simulate_container(command: List[str]) -> subprocess.CompletedProcess:
    """Simulate container execution by running the command with safety wrappers."""

    LOGGER.info("Simulating container run: %s", command)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd())
    return subprocess.run(
        command,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=SETTINGS.runtime.max_runtime_seconds,
    )


def run_agent_subprocess(agent_module: str, agent_class: str, sandbox: SandboxPaths) -> subprocess.CompletedProcess:
    """Run an agent inside a sandboxed subprocess."""

    command = [
        sys.executable,
        "-m",
        "government.worker",
        agent_module,
        agent_class,
        str(sandbox.root),
    ]
    LOGGER.info("Launching agent subprocess for %s", agent_class)
    return simulate_container(command)


__all__ = ["SandboxPaths", "simulate_container", "run_agent_subprocess"]
