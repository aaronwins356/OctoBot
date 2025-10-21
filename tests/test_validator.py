from __future__ import annotations

import pytest

from laws.validator import LawValidator, LawViolation


def test_validator_detects_missing_approval(tmp_path) -> None:
    validator = LawValidator()
    with pytest.raises(LawViolation):
        validator.ensure(["rationale logged"])


def test_validator_passes_with_approval(tmp_path) -> None:
    validator = LawValidator()
    validator.ensure(["human approval", "rationale logged"])
