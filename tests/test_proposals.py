"""Tests for proposal packaging and PR drafting."""
from __future__ import annotations

from government import proposals
from government.proposals import ProposalRecord, draft_pull_request, package_proposal


def test_package_proposal_creates_directory() -> None:
    record = package_proposal("WriterAgent", {"README.txt": "hello"}, summary="Test")
    assert record.path.exists()
    assert (record.path / "README.txt").read_text(encoding="utf-8") == "hello"
    for path in record.path.rglob("*"):
        if path.is_file():
            path.unlink()
    record.path.rmdir()


def test_draft_pull_request_offline(monkeypatch) -> None:
    record = package_proposal("WriterAgent", {"notes.txt": "data"})

    called = {}

    def fake_create(record: ProposalRecord, body: str):
        called["body"] = body
        return "http://example.com/pr"

    monkeypatch.setattr(proposals, "_create_github_pr", fake_create)
    updated = draft_pull_request(record, {"status": "ok"})
    assert updated.draft_pr_url == "http://example.com/pr"
    assert "WriterAgent" in called["body"]
    for path in record.path.rglob("*"):
        if path.is_file():
            path.unlink()
    record.path.rmdir()
