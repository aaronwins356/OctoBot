"""Subprocess entrypoint for executing a single agent in isolation."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from entrepreneurs.base_agent import BaseAgent
from utils.logger import get_logger

LOGGER = get_logger(__name__)


def _load_agent(module_name: str, class_name: str) -> type[BaseAgent]:
    module = importlib.import_module(module_name)
    agent_cls = getattr(module, class_name)
    if not issubclass(agent_cls, BaseAgent):  # pragma: no cover - safety check
        raise TypeError(f"{class_name} is not a BaseAgent")
    return agent_cls


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) != 3:
        raise SystemExit("Usage: worker.py <module> <class> <sandbox>")
    module_name, class_name, sandbox_path = argv
    sandbox = Path(sandbox_path)
    sandbox.mkdir(parents=True, exist_ok=True)

    agent_cls = _load_agent(module_name, class_name)
    agent = agent_cls(name=class_name, sandbox_path=str(sandbox))

    LOGGER.info("Worker starting agent %s", class_name)
    agent.setup()
    output = agent.run({})
    report = agent.report()

    payload = {"output": output, "report": report}
    print(json.dumps(payload))
    LOGGER.info("Worker finished agent %s", class_name)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
