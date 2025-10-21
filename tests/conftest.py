from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from octobot.memory.utils import proposals_root, repo_root


@pytest.fixture(autouse=True)
def reset_runtime(tmp_path: Path) -> None:
    proposals_dir = proposals_root()
    for child in proposals_dir.iterdir():
        if child.name == "_workspace":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    workspace = proposals_dir / "_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "coverage.json").write_text(json.dumps({"coverage": 0.95}), encoding="utf-8")
    ledger_path = repo_root() / "memory" / "ledger.json"
    if ledger_path.exists():
        ledger_path.unlink()
