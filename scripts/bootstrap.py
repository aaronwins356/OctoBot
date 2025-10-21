"""Bootstrap OctoBot with an initial improvement cycle."""
from __future__ import annotations

from octobot.core.orchestrator import Orchestrator


def main() -> None:
    orchestrator = Orchestrator()
    lifecycle = orchestrator.draft_proposal("Bootstrap Improvements")
    print("Generated proposal:", lifecycle.proposal.proposal_id)
    if lifecycle.validation:
        print("Validation status:", "compliant" if lifecycle.validation.compliant else "issues detected")
    if lifecycle.evaluation:
        print("Evaluation complexity score:", lifecycle.evaluation.complexity)


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()
