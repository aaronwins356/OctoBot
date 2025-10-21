from __future__ import annotations

from pathlib import Path

import pytest

from interface.dashboard import Flask, create_app
from government.proposal_manager import ProposalManager
from memory.history_logger import HistoryLogger


def test_dashboard_home_route(tmp_path: Path) -> None:
    if Flask is None:
        pytest.skip("Flask not installed")

    manager = ProposalManager(repo_root=tmp_path)
    # Ensure at least one proposal exists
    report = {
        "findings": [],
        "unused_imports": 0,
        "missing_docstrings": 0,
        "files_scanned": 0,
    }
    manager.generate(report)
    app = create_app(proposal_manager=manager, logger=HistoryLogger())
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
