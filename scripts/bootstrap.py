"""Bootstrap OctoBot with an initial improvement cycle."""
from __future__ import annotations

from government.orchestrator import Orchestrator


def main() -> None:
    orchestrator = Orchestrator()
    result = orchestrator.run_cycle()
    print("Analyzer report at:", result.report_path)
    for proposal in result.proposals:
        print("Generated proposal:", proposal.proposal_id)


if __name__ == "__main__":
    main()
