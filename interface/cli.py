"""Command-line utilities for supervising venture proposals."""
from __future__ import annotations

import argparse
from pathlib import Path

from entrepreneurs.venture_agent import VentureAgent
from government.presenter import build_portfolio
from government.proposal_manager import (
    load_proposals,
    mark_proposal_status,
)
from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


def _sandbox_path() -> Path:
    root = Path(SETTINGS.runtime.sandbox_root)
    target = root / "venture_agent"
    target.mkdir(parents=True, exist_ok=True)
    return target


def generate_venture() -> None:
    LOGGER.info("Triggering venture agent to draft a new proposal")
    agent = VentureAgent("venture_agent", str(_sandbox_path()))
    agent.setup()
    result = agent.run({})
    LOGGER.info("Generated proposal at %s", result["proposal_manifest"])
    print(result["proposal_manifest"])


def list_proposals() -> None:
    proposals = load_proposals()
    for proposal in proposals:
        status = proposal.status
        print(f"{proposal.storage_path.name if proposal.storage_path else proposal.proposal_id}: {status}")


def show_proposal(identifier: str) -> None:
    for proposal in load_proposals():
        folder_name = proposal.storage_path.name if proposal.storage_path else proposal.proposal_id
        if folder_name == identifier or proposal.proposal_id == identifier:
            manifest = proposal.storage_path / "proposal.yaml" if proposal.storage_path else None
            if manifest and manifest.exists():
                print(manifest.read_text(encoding="utf-8"))
                return
    raise FileNotFoundError(f"Proposal {identifier} not found")


def approve_proposal(identifier: str) -> None:
    for proposal in load_proposals():
        folder_name = proposal.storage_path.name if proposal.storage_path else proposal.proposal_id
        if folder_name == identifier or proposal.proposal_id == identifier:
            mark_proposal_status(proposal, "approved")
            LOGGER.info("Proposal %s approved", identifier)
            print(f"Approved {identifier}")
            return
    raise FileNotFoundError(f"Proposal {identifier} not found")


def publish_site() -> None:
    created = build_portfolio()
    LOGGER.info("Site generated with %d files", len(created))
    for path in created:
        print(path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grounded Lifestyle supervision CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("generate-venture")
    sub.add_parser("list-proposals")

    show_parser = sub.add_parser("show")
    show_parser.add_argument("identifier")

    approve_parser = sub.add_parser("approve")
    approve_parser.add_argument("identifier")

    sub.add_parser("publish-site")

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "generate-venture":
        generate_venture()
    elif args.command == "list-proposals":
        list_proposals()
    elif args.command == "show":
        show_proposal(args.identifier)
    elif args.command == "approve":
        approve_proposal(args.identifier)
    elif args.command == "publish-site":
        publish_site()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
