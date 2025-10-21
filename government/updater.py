"""Apply approved proposals through Git."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from git import Repo

from laws.validator import DEFAULT_VALIDATOR, LawViolation
from memory.history_logger import HistoryLogger


class Updater:
    def __init__(self, repo_root: Path | None = None, logger: HistoryLogger | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.logger = logger or HistoryLogger()

    def merge(self, proposal_id: str, message: Optional[str] = None) -> str:
        DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
        if not self.logger.is_approved(proposal_id):
            raise LawViolation(f"Proposal {proposal_id} has not been approved.")
        repo = Repo(self.repo_root)
        repo.git.add(A=True)
        commit_message = message or f"Apply proposal {proposal_id}"
        commit = repo.index.commit(commit_message)
        self.logger.log_event(f"Updater merged proposal {proposal_id} with commit {commit.hexsha}")
        return commit.hexsha
