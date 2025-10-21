"""Command line interface for OctoBot."""
from __future__ import annotations

import json

import click

from government.orchestrator import Orchestrator
from government.proposal_manager import ProposalManager
from laws.validator import enforce
from memory.utils import proposals_root
from website.app import create_app


@click.group(name="octobot")
def cli() -> None:
    """Supervise the OctoBot proposal pipeline."""


@cli.command()
@click.argument("topic")
def propose(topic: str) -> None:
    """Run the full analysis and proposal pipeline for *TOPIC*."""
    enforce("filesystem_write", str(proposals_root()))
    orchestrator = Orchestrator()
    result = orchestrator.run_cycle(topic)
    click.echo(f"Proposal {result.proposal.proposal_id} generated for topic '{topic}'.")


@cli.command()
@click.argument("proposal_id")
def evaluate(proposal_id: str) -> None:
    """Display evaluation metadata for *PROPOSAL_ID*."""
    manager = ProposalManager()
    proposal = manager.load(proposal_id)
    if not proposal:
        click.echo("Proposal not found.")
        raise SystemExit(1)
    click.echo(json.dumps({
        "id": proposal.proposal_id,
        "status": proposal.status,
        "coverage": proposal.coverage,
        "summary": proposal.summary,
    }, indent=2))


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
    """Record human approval for *PROPOSAL_ID*."""
    ProposalManager().approve(proposal_id, approver)
    click.echo(f"Proposal {proposal_id} approved by {approver}.")


@cli.command()
@click.argument("proposal_id")
def apply(proposal_id: str) -> None:
    """Apply an approved proposal."""
    orchestrator = Orchestrator()
    commit = orchestrator.apply_if_approved(proposal_id)
    if not commit:
        click.echo("Proposal is not approved or does not exist.")
        raise SystemExit(1)
    click.echo(f"Applied proposal {proposal_id} with commit {commit}.")


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=5000, show_default=True, type=int)
def dashboard(host: str, port: int) -> None:
    """Run the OctoBot dashboard."""
    app = create_app()
    app.run(host=host, port=port)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
