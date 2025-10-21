from __future__ import annotations

import octobot.laws.validator as validator


def test_law_enforced_invokes_enforce(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_enforce(rule: str, context: str) -> bool:
        calls.append((rule, context))
        return True

    monkeypatch.setattr(validator, "enforce", fake_enforce)

    @validator.law_enforced("external_request")
    def sample() -> str:
        return "ok"

    assert sample() == "ok"
    assert calls
    assert calls[0][0] == "external_request"
    assert calls[0][1].endswith(".py")


def test_law_enforced_default_no_call(monkeypatch) -> None:
    def fake_enforce(rule: str, context: str) -> bool:
        raise AssertionError("enforce should not be called for default rule")

    monkeypatch.setattr(validator, "enforce", fake_enforce)

    @validator.law_enforced()
    def sample() -> str:
        return "ok"

    assert sample() == "ok"
