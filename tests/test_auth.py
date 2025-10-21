import importlib

import pytest
from fastapi import HTTPException

from octobot.security import auth_shared


def test_verify_token_requires_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCTOBOT_KEY", raising=False)
    importlib.reload(auth_shared)
    with pytest.raises(HTTPException) as exc:
        auth_shared.verify_token("ignored")
    assert exc.value.status_code == 500


def test_verify_token_accepts_matching_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCTOBOT_KEY", "secret")
    importlib.reload(auth_shared)
    assert auth_shared.verify_token("secret") == "secret"


def test_verify_token_rejects_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCTOBOT_KEY", "secret")
    importlib.reload(auth_shared)
    with pytest.raises(HTTPException) as exc:
        auth_shared.verify_token("nope")
    assert exc.value.status_code == 401
    monkeypatch.delenv("OCTOBOT_KEY", raising=False)
