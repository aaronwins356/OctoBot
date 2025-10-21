from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from octobot.core.evaluator import Evaluator, _to_float
from octobot.core.proposal_manager import ProposalManager
from octobot.interface.cli import evaluate
from octobot.memory.utils import load_yaml


def test_coverage_normalisation_across_components() -> None:
    manager = ProposalManager()
    analysis = {
        "findings": [],
        "coverage": 0.91,
        "todos": 0,
        "missing_docstrings": 0,
        "complexity_average": 3.0,
    }
    proposal = manager.generate("Normalise Coverage", analysis)
    manager.mark_ready_for_review(proposal.proposal_id, 95.0)

    metadata = load_yaml(proposal.path / "proposal.yaml")
    assert pytest.approx(0.95, rel=1e-6) == metadata["coverage"]

    listed = manager.list_proposals()
    assert listed[0].coverage <= 1

    runner = CliRunner()
    result = runner.invoke(evaluate, [proposal.proposal_id])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert pytest.approx(95.0, rel=1e-6) == payload["coverage_percent"]
    assert pytest.approx(0.95, rel=1e-6) == payload["coverage_fraction"]


def test_evaluator_accepts_percentage_inputs() -> None:
    evaluator = Evaluator()
    evaluations = evaluator.score(
        [
            {
                "id": "p1",
                "summary": "Refactor docs module",  # triggers both doc and refactor logic
                "coverage": 95,
            }
        ]
    )
    assert evaluations
    record = evaluations[0]
    assert pytest.approx(0.95, rel=1e-6) == record.tests
    assert pytest.approx(0.3, rel=1e-6) == record.risk


def test_to_float_handles_strings() -> None:
    assert pytest.approx(0.25) == _to_float("0.25")
    assert _to_float("n/a") == 0.0
