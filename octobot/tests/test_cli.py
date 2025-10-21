from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from octobot.interface.cli import cli
from octobot.memory.utils import proposals_root


def test_cli_proposal_flow(tmp_path: Path) -> None:
    workspace = proposals_root() / "_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "coverage.json").write_text(json.dumps({"coverage": 0.95}), encoding="utf-8")

    runner = CliRunner()
    propose_result = runner.invoke(cli, ["propose", "CLI Improvements"])
    assert propose_result.exit_code == 0

    proposals_output = runner.invoke(cli, ["list-proposals"])
    assert "CLI Improvements" in proposals_output.output

    lines = [line for line in proposals_output.output.splitlines() if line.strip()]
    proposal_id = lines[-1].split("\t")[0]

    evaluate_result = runner.invoke(cli, ["evaluate", proposal_id])
    assert evaluate_result.exit_code == 0
    assert "status" in evaluate_result.output

    approve_output = runner.invoke(
        cli,
        ["approve", proposal_id, "--approver", "tester"],
        env={"OCTOBOT_DRY_RUN": "1"},
    )
    assert approve_output.exit_code == 0
