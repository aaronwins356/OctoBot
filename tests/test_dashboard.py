import importlib

import pytest
from fastapi.testclient import TestClient

from octobot.interface.dashboard import create_app
from octobot.core.proposals import ProposalManager
from octobot.security import auth_shared


@pytest.fixture
def app(tmp_path):
    application = create_app()
    application.state.proposal_manager = ProposalManager(store_path=tmp_path / "proposals.json")
    return application


def test_index_lists_proposals(app):
    manager = app.state.proposal_manager
    proposal = manager.create("Hello", {"coverage": 0.95})

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello" in response.text


def test_approve_and_reject_routes(app, monkeypatch):
    monkeypatch.setenv("OCTOBOT_KEY", "secret")
    importlib.reload(auth_shared)
    # FastAPI keeps a reference to verify_token imported earlier; update module state
    auth_shared.OCTOBOT_KEY = "secret"
    manager = app.state.proposal_manager
    proposal = manager.create("World", {"coverage": 0.95})

    client = TestClient(app)
    approved = client.post(f"/approve/{proposal.id}", headers={"x-api-key": "secret"})
    assert approved.status_code == 200
    payload = approved.json()
    assert payload["status"] == "approved"

    rejected = client.post(f"/reject/{proposal.id}", headers={"x-api-key": "secret"})
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    monkeypatch.delenv("OCTOBOT_KEY", raising=False)
