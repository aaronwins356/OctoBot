"""Command line interface for The Brain."""
from __future__ import annotations

import json
from dataclasses import asdict
import typer

from interface.api_server import orchestrator

app = typer.Typer(help="Interact with The Brain from the terminal.")


@app.command()
def execute(goal: str) -> None:
    """Execute a goal and print the resulting plan and insights."""

    result = orchestrator.execute_goal(goal)
    typer.echo("Plan:")
    typer.echo(json.dumps(result["plan"].to_dict(), indent=2))
    typer.echo("Results:")
    for evaluation in result["results"]:
        typer.echo(json.dumps(asdict(evaluation), indent=2))
    typer.echo("Insights:")
    typer.echo(result["insights"])


@app.command()
def generate(prompt: str) -> None:
    """Generate a response using the local language model."""

    response = orchestrator.llm_client.generate(prompt)
    typer.echo(response)


if __name__ == "__main__":
    app()
