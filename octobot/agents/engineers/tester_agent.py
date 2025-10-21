"""Wrapper around pytest execution."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict

from octobot.laws.validator import enforce, guard, register_agent
from octobot.memory.logger import log_event

register_agent("tester")


class TesterAgent:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    @guard("tester")
    def run_tests(self) -> Dict[str, str | int]:
        enforce("filesystem_write", str(self.repo_root / "proposals"))
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("OCTOBOT_ALLOW_TEST_SKIP"):
            log_event("tester", "pytest", "skipped", "running inside pytest or skip allowed")
            return {
                "status": "skipped",
                "output": "Tests skipped due to nested pytest execution.",
                "returncode": 0,
            }
        try:
            completed = subprocess.run(
                ["pytest", "-q"],
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            status = "passed" if completed.returncode == 0 else "failed"
            log_event("tester", "pytest", status, completed.stdout)
            return {
                "status": status,
                "output": completed.stdout,
                "returncode": completed.returncode,
            }
        except FileNotFoundError:
            log_event("tester", "pytest", "skipped", "pytest not installed")
            return {
                "status": "skipped",
                "output": "pytest not installed",
                "returncode": -1,
            }
