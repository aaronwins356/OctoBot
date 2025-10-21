"""Apply approved proposals."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from octobot.core.proposal_manager import Proposal
from octobot.laws.validator import enforce
from octobot.memory.logger import log_event
from octobot.memory.utils import repo_root, timestamp


class Updater:
    """Apply proposal patches once human approval is recorded."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or repo_root()

    def apply(self, proposal: Proposal) -> str:
        enforce("code_merge", "approved")
        diff_path = proposal.path / "diff.patch"
        if not diff_path.exists():
            raise FileNotFoundError(f"Missing diff at {diff_path}")
        log_event("updater", "apply", "started", {"proposal": proposal.proposal_id})
        self._apply_patch(diff_path)
        commit_sha = self._commit(proposal)
        self._tag_release(proposal, commit_sha)
        log_event(
            "updater",
            "apply",
            "completed",
            {"proposal": proposal.proposal_id, "commit": commit_sha},
        )
        return commit_sha

    def _apply_patch(self, diff_path: Path) -> None:
        env = {**os.environ}
        process = subprocess.run(
            ["git", "apply", str(diff_path)],
            cwd=self.root,
            check=False,
            capture_output=True,
            env=env,
        )
        if process.returncode != 0:
            log_event("updater", "apply_patch", "failed", process.stderr.decode())
            raise RuntimeError(f"Failed to apply patch: {process.stderr.decode()}")
        log_event("updater", "apply_patch", "success", diff_path.name)

    def _commit(self, proposal: Proposal) -> str:
        message = f"Apply proposal {proposal.proposal_id}"
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "OctoBot",
            "GIT_AUTHOR_EMAIL": "octobot@example.com",
            "GIT_COMMITTER_NAME": "OctoBot",
            "GIT_COMMITTER_EMAIL": "octobot@example.com",
        }
        process = subprocess.run(
            ["git", "add", "-A"],
            cwd=self.root,
            check=False,
            capture_output=True,
            env=env,
        )
        if process.returncode != 0:
            raise RuntimeError(process.stderr.decode())
        commit = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.root,
            check=False,
            capture_output=True,
            env=env,
        )
        if commit.returncode != 0:
            raise RuntimeError(commit.stderr.decode())
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root).decode().strip()
        return sha

    def _tag_release(self, proposal: Proposal, sha: str) -> None:
        date_segment = timestamp().split("T")[0].replace("-", ".")
        topic_segment = proposal.topic.replace(" ", "_")
        tag = f"v{date_segment}_{topic_segment}"
        subprocess.run(["git", "tag", tag, sha], cwd=self.root, check=False, env=os.environ)
        log_event("updater", "tag", "created", {"tag": tag, "sha": sha})
