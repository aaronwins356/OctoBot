"""Command line interface for OctoBot."""
from __future__ import annotations

import json
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from engineers.analyzer_agent import AnalyzerAgent
from government.evaluator import Evaluator
from government.proposal_manager import ProposalManager
from interface.dashboard import create_app
from laws.validator import DEFAULT_VALIDATOR
from memory.history_logger import HistoryLogger

console = Console()


@click.group()
def cli() -> None:
    """OctoBot supervision interface."""


@cli.command()
def analyze() -> None:
    """Scan the repository and produce an analyzer report."""
    DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
    report = AnalyzerAgent().scan_repo()
    console.print("Analyzer report saved to reports/analyzer_report.json")
    console.print(json.dumps(report, indent=2))


@cli.command()
def propose() -> None:
    """Generate proposals based on the latest analyzer report."""
    DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
    analyzer = AnalyzerAgent()
    report = analyzer.scan_repo()
    proposals = ProposalManager().generate(report)
    table = Table(title="Generated Proposals")
    table.add_column("ID")
    table.add_column("Impact")
    table.add_column("Risk")
    table.add_column("Summary")
    for proposal in proposals:
        table.add_row(proposal.proposal_id, proposal.impact, proposal.risk, proposal.summary)
    console.print(table)


@cli.command()
def evaluate() -> None:
    """Evaluate current proposals and display scores."""
    DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
    manager = ProposalManager()
    proposals = manager.list_proposals()
    evaluations = Evaluator().score([proposal.__dict__ | {"id": proposal.proposal_id} for proposal in proposals])
    table = Table(title="Evaluation Scores")
    table.add_column("Proposal")
    table.add_column("Complexity")
    table.add_column("Tests")
    table.add_column("Docs")
    table.add_column("Risk")
    for evaluation in evaluations:
        table.add_row(
            evaluation.proposal_id,
            f"{evaluation.complexity:.2f}",
            f"{evaluation.tests:.2f}",
            f"{evaluation.docs:.2f}",
            f"{evaluation.risk:.2f}",
        )
    console.print(table)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host address")
@click.option("--port", default=5000, type=int, help="Port number")
def serve(host: str, port: int) -> None:
    """Launch the OctoBot dashboard."""
    DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
    app = create_app()
    app.run(host=host, port=port)


@cli.command()
@click.argument("proposal_id")
@click.option("--approver", default="cli", help="Name of the approver")
def approve(proposal_id: str, approver: str) -> None:
    """Record approval for a proposal."""
    DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
    HistoryLogger().approve(proposal_id, approver)
    console.print(f"Proposal {proposal_id} approved by {approver}")


@cli.command(name="log")
def show_log() -> None:
    """Display recent history events."""
    DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
    events = HistoryLogger().list_events()
    table = Table(title="History Events")
    table.add_column("Timestamp")
    table.add_column("Event")
    for event, timestamp in events:
        table.add_row(timestamp, event)
    console.print(table)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
