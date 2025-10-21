"""Main orchestrator coordinating agent execution and governance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict

import memory
from economy import ledger
from government.models import AgentExecutionResult, AgentRegistration
from government.proposals import draft_pull_request, package_proposal
from government.registry import discover_agents
from government.sandbox import SandboxPaths, run_agent_subprocess
from laws.audit import log_event
from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


def _hash_payload(payload: str) -> str:
    digest = hashlib.sha256()
    digest.update(payload.encode("utf-8"))
    return digest.hexdigest()


def _handle_proposal(agent_name: str, data: Dict[str, Dict[str, str]]) -> None:
    files = data.get("files", {})
    summary = data.get("summary", "")
    record = package_proposal(agent_name, files, summary)
    evaluation = {"status": "pending", "notes": "Awaiting human review"}
    draft_pull_request(record, evaluation)


def run_all_agents(dry_run: bool = True) -> None:
    """Orchestrates discovery, verification, sandbox execution, evaluation, audit logging, and memory storage.
    If dry_run is True, do not execute agents — only run static checks and simulate runs.
    """

    entrepreneurs_path = Path("entrepreneurs")
    agent_classes = discover_agents(entrepreneurs_path)
    LOGGER.info("Discovered %d agents", len(agent_classes))

    for agent_cls in agent_classes:
        agent_name = agent_cls.__name__
        module_name = agent_cls.__module__
        sandbox = SandboxPaths.create(agent_name.lower())
        module_path = Path(getattr(agent_cls, '__source_path__', entrepreneurs_path / f'{agent_name.lower()}.py'))
        registration = AgentRegistration(
            name=agent_name,
            module_path=module_path,
            sandbox_path=sandbox.root,
        )
        ledger.add_agent(agent_name)

        if dry_run:
            LOGGER.info("Dry run - validated agent %s without execution", agent_name)
            memory.store_event(agent_name, {"status": "validated", "sandbox": str(sandbox.root)})
            continue

        result = run_agent_subprocess(module_name, agent_name, sandbox)
        success = result.returncode == 0
        output_data: Dict[str, Dict[str, str]] = {}
        report_data: Dict[str, str] = {}
        if success and result.stdout:
            try:
                payload = json.loads(result.stdout)
                output_data = payload.get("output", {})
                report_data = payload.get("report", {})
            except json.JSONDecodeError as exc:
                LOGGER.error("Failed to decode agent output for %s: %s", agent_name, exc)
                success = False
        else:
            LOGGER.error("Agent %s failed with code %s", agent_name, result.returncode)

        result_hash = _hash_payload(result.stdout or "")
        log_event(agent_name, "run", registration.module_path, result_hash)

        execution = AgentExecutionResult(
            name=agent_name,
            success=success,
            output=output_data,
            report=report_data,
            sandbox_path=sandbox.root,
        )
        memory.store_event(agent_name, execution.dict())
        if success:
            ledger.add_credits(agent_name, SETTINGS.simulation.reward_per_success)

        if output_data.get("proposal"):
            _handle_proposal(agent_name, output_data["proposal"])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI Republic orchestrator")
    parser.add_argument("--live", action="store_true", help="Execute agents (default is dry-run)")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_all_agents(dry_run=not args.live)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
