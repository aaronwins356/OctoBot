"""Human approval CLI for inspecting and approving proposals."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from laws.static_checks import run_static_checks
from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


def _proposal_root() -> Path:
    root = Path(SETTINGS.runtime.proposal_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def list_proposals() -> List[str]:
    proposals = sorted(p.name for p in _proposal_root().iterdir() if p.is_dir())
    LOGGER.info("Listing %d proposals", len(proposals))
    return proposals


def show_proposal(id: str) -> None:
    proposal_path = _proposal_root() / id
    if not proposal_path.exists():
        raise FileNotFoundError(f"Proposal {id} not found")
    LOGGER.info("Showing proposal %s", id)
    for path in sorted(proposal_path.rglob("*")):
        if path.is_file():
            print(f"== {path.relative_to(proposal_path)} ==")
            print(path.read_text(encoding="utf-8"))


def run_proposal_tests(id: str) -> None:
    proposal_path = _proposal_root() / id
    python_files = list(proposal_path.rglob("*.py"))
    if python_files:
        run_static_checks(python_files)
        LOGGER.info("Static checks passed for proposal %s", id)
    else:
        LOGGER.info("No Python files to test for proposal %s", id)


def approve_proposal(id: str, reviewer: str) -> None:
    proposal_path = _proposal_root() / id
    if not proposal_path.exists():
        raise FileNotFoundError(f"Proposal {id} not found")
    LOGGER.info("Reviewer %s approving proposal %s", reviewer, id)
    print("Manual approval steps:")
    print("1. git checkout -b review/%s" % id)
    print("2. cp -R %s/* ." % proposal_path)
    print("3. git status")
    print("4. make test && make lint")
    print("5. git commit -am \"Apply proposal %s\"" % id)
    print("6. git push origin review/%s" % id)
    print("7. Open PR and request approvals (do not auto-merge)")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Republic human approval CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-proposals")

    show_parser = sub.add_parser("show-proposal")
    show_parser.add_argument("id")

    test_parser = sub.add_parser("run-proposal-tests")
    test_parser.add_argument("id")

    approve_parser = sub.add_parser("approve-proposal")
    approve_parser.add_argument("id")
    approve_parser.add_argument("--reviewer", required=True)

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "list-proposals":
        for item in list_proposals():
            print(item)
    elif args.command == "show-proposal":
        show_proposal(args.id)
    elif args.command == "run-proposal-tests":
        run_proposal_tests(args.id)
    elif args.command == "approve-proposal":
        approve_proposal(args.id, args.reviewer)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
