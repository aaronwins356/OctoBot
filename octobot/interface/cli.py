"""Command line interface for supervising OctoBot."""
from __future__ import annotations

import json
from pathlib import Path

import click

from octobot.core.evaluator import Evaluator
from octobot.core.orchestrator import Orchestrator
from octobot.core.proposal_manager import ProposalManager
from octobot.laws.validator import enforce
from octobot.memory.utils import proposals_root
from octobot.interface.dashboard import create_app


@click.group(name="octobot")
def cli() -> None:
    """Supervise the OctoBot proposal pipeline."""


@cli.command()
@click.argument("topic")
@click.option("--proposer", default="engineers", show_default=True)
def propose(topic: str, proposer: str) -> None:
    """Run analysis and draft a proposal for *TOPIC*."""

    enforce("filesystem_write", str(proposals_root()))
    orchestrator = Orchestrator()
    lifecycle = orchestrator.draft_proposal(topic, proposer=proposer)
    click.echo(f"Proposal {lifecycle.proposal.proposal_id} generated for topic '{topic}'.")
    if lifecycle.validation:
        status = "compliant" if lifecycle.validation.compliant else "violations"
        click.echo(f"Validation: {status}")
        if lifecycle.validation.issues:
            click.echo(" - " + "\n - ".join(lifecycle.validation.issues))
    if lifecycle.evaluation:
        click.echo(
            "Evaluation: complexity={:.2f} tests={:.2f} docs={:.2f} risk={:.2f}".format(
                lifecycle.evaluation.complexity,
                lifecycle.evaluation.tests,
                lifecycle.evaluation.docs,
                lifecycle.evaluation.risk,
            )
        )


@cli.command()
@click.argument("proposal_id")
def evaluate(proposal_id: str) -> None:
    """Display evaluation metadata for *PROPOSAL_ID*."""

    manager = ProposalManager()
    proposal = manager.load(proposal_id)
    if not proposal:
        click.echo("Proposal not found.")
        raise SystemExit(1)
    coverage = proposal.coverage if proposal.coverage > 1 else proposal.coverage * 100
    evaluator = Evaluator()
    evaluation = evaluator.score(
        [
            {
                "id": proposal.proposal_id,
                "summary": proposal.summary,
                "coverage": coverage,
            }
        ]
    )
    payload = {
        "id": proposal.proposal_id,
        "status": proposal.status,
        "coverage": coverage,
        "summary": proposal.summary,
    }
    if evaluation:
        payload["evaluation"] = {
            "complexity": evaluation[0].complexity,
            "tests": evaluation[0].tests,
            "docs": evaluation[0].docs,
            "risk": evaluation[0].risk,
        }
    click.echo(json.dumps(payload, indent=2))


@cli.command(name="list-proposals")
def list_proposals() -> None:
    """List all known proposals."""

    proposals = ProposalManager().list_proposals()
    for proposal in proposals:
        click.echo(f"{proposal.proposal_id}\t{proposal.status}\t{proposal.summary}")


@cli.command()
@click.argument("proposal_id")
def show(proposal_id: str) -> None:
    """Show detailed content of a proposal."""

    proposal = ProposalManager().load(proposal_id)
    if not proposal:
        click.echo("Proposal not found")
        raise SystemExit(1)
    metadata = proposal.path / "proposal.yaml"
    rationale = proposal.path / "rationale.md"
    click.echo(metadata.read_text(encoding="utf-8"))
    click.echo("\n--- RATIONALE ---\n")
    click.echo(rationale.read_text(encoding="utf-8"))


@cli.command()
@click.argument("proposal_id")
@click.option("--approver", default="cli", show_default=True)
def approve(proposal_id: str, approver: str) -> None:
    """Record human approval and apply *PROPOSAL_ID*."""

    orchestrator = Orchestrator()
    commit = orchestrator.approve_proposal(proposal_id, approver)
    if not commit:
        click.echo("Approval failed or tests did not pass; review logs for details.")
        raise SystemExit(1)
    click.echo(f"Proposal {proposal_id} applied with commit {commit}.")


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
def dashboard(host: str, port: int) -> None:
    """Run the OctoBot FastAPI dashboard."""

    app = create_app()
    import uvicorn  # Imported lazily to avoid dependency at import time

    uvicorn.run(app, host=host, port=port)


def main() -> None:
    cli()


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
