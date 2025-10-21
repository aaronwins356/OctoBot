"""Testing automation for OctoBot."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict

from laws.validator import DEFAULT_VALIDATOR
from memory.history_logger import HistoryLogger


class TesterAgent:
    def __init__(self, repo_root: Path | None = None, logger: HistoryLogger | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.logger = logger or HistoryLogger()

    def run_tests(self) -> Dict[str, str | int]:
        DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
        try:
            completed = subprocess.run(
                ["pytest", "-q"],
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            success = completed.returncode == 0
            self.logger.log_event("Tester agent executed pytest with success=%s" % success)
            return {
                "status": "passed" if success else "failed",
                "output": completed.stdout,
                "returncode": completed.returncode,
            }
        except FileNotFoundError:
            self.logger.log_event("Pytest not available; returning skipped status")
            return {
                "status": "skipped",
                "output": "pytest not installed",
                "returncode": -1,
            }
