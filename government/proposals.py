"""Proposal management including packaging and optional PR drafting."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

import requests

from laws import enforcement
from laws.static_checks import run_static_checks
from utils.logger import get_logger
from utils.settings import SETTINGS

from .models import ProposalRecord

LOGGER = get_logger(__name__)


def _proposal_dir() -> Path:
    proposal_dir = Path(SETTINGS.runtime.proposal_dir)
    proposal_dir.mkdir(parents=True, exist_ok=True)
    return proposal_dir


def package_proposal(agent: str, files: Dict[str, str], summary: str = "") -> ProposalRecord:
    timestamp = int(time.time())
    proposal_id = f"{timestamp}_{agent}"
    proposal_root = _proposal_dir() / proposal_id
    proposal_root.mkdir(parents=True, exist_ok=True)

    saved_paths: List[Path] = []
    for relative, content in files.items():
        target = proposal_root / relative
        enforcement.verify_agent_permissions(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        saved_paths.append(target)

    python_files = [p for p in saved_paths if p.suffix == ".py"]
    if python_files:
        run_static_checks(python_files)

    record = ProposalRecord(
        proposal_id=proposal_id,
        agent=agent,
        path=proposal_root,
        summary=summary,
    )
    LOGGER.info("Packaged proposal %s for agent %s", proposal_id, agent)
    return record


def _github_headers() -> Dict[str, str]:
    token = SETTINGS.github_token
    if not token:
        return {}
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _create_github_pr(record: ProposalRecord, body: str) -> str | None:
    if SETTINGS.offline_mode or not SETTINGS.github_token or not SETTINGS.github_repository:
        LOGGER.info("Offline mode - storing draft PR locally for %s", record.proposal_id)
        local_draft = record.path / "draft_pr.json"
        local_draft.write_text(body, encoding="utf-8")
        return None

    url = f"{SETTINGS.network.github_api_url}/repos/{SETTINGS.github_repository}/pulls"
    data = {
        "title": f"Draft: Proposal {record.proposal_id}",
        "head": f"proposal/{record.proposal_id}",
        "base": "main",
        "body": body,
        "draft": True,
    }
    response = requests.post(url, headers=_github_headers(), json=data, timeout=10)
    response.raise_for_status()
    pr_url = response.json().get("html_url")
    LOGGER.info("Created draft PR at %s", pr_url)
    return pr_url


def draft_pull_request(record: ProposalRecord, evaluation: Dict[str, str]) -> ProposalRecord:
    body = json.dumps(
        {
            "proposal": record.proposal_id,
            "agent": record.agent,
            "summary": record.summary,
            "evaluation": evaluation,
        },
        indent=2,
    )
    pr_url = _create_github_pr(record, body)
    record.draft_pr_url = pr_url
    return record


__all__ = ["package_proposal", "draft_pull_request"]
