"""Agent discovery registry for the AI Republic government."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import List, Type

from entrepreneurs.base_agent import BaseAgent
from laws.enforcement import verify_agent_code
from utils.logger import get_logger

LOGGER = get_logger(__name__)


def _load_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import module {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_agents(path: Path) -> List[Type[BaseAgent]]:
    """Dynamically discover BaseAgent subclasses under entrepreneurs/ but do not import unsafe modules."""

    agents: List[Type[BaseAgent]] = []
    for file in path.glob("*.py"):
        if file.name in {"__init__.py", "base_agent.py"}:
            continue
        verify_agent_code(file)
        module_name = f"entrepreneurs.{file.stem}"
        module = _load_module_from_path(module_name, file)
        for attribute in module.__dict__.values():
            if isinstance(attribute, type) and issubclass(attribute, BaseAgent) and attribute is not BaseAgent:
                setattr(attribute, "__source_path__", file)
                agents.append(attribute)
                LOGGER.info("Discovered agent %s from %s", attribute.__name__, file)
    return agents


__all__ = ["discover_agents"]
