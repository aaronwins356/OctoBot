"""AST-based validation routines for entrepreneur agents and proposals."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


@dataclass
class ValidationResult:
    """Structure describing the outcome of a validation pass."""

    errors: List[str]

    @property
    def ok(self) -> bool:
        return not self.errors


class _LawVisitor(ast.NodeVisitor):
    def __init__(self, constitution: dict):
        self.constitution = constitution
        self.errors: List[str] = []
        self.forbidden_calls = set(constitution.get("forbidden_calls", [])) | set(
            SETTINGS.security.forbidden_calls
        )
        self.forbidden_imports = set(constitution.get("forbidden_imports", [])) | set(
            SETTINGS.security.disallowed_imports
        )

    def _record(self, message: str) -> None:
        LOGGER.warning("Validation issue: %s", message)
        self.errors.append(message)

    def visit_Import(self, node: ast.Import) -> None:  # pragma: no cover - simple
        for alias in node.names:
            name = alias.name.split(".")[0]
            if name in self.forbidden_imports:
                self._record(f"Forbidden import: {name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = (node.module or "").split(".")[0]
        if module in self.forbidden_imports:
            self._record(f"Forbidden import from: {module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            qualname = f"{ast.unparse(node.func.value)}.{node.func.attr}"  # type: ignore[arg-type]
        elif isinstance(node.func, ast.Name):
            qualname = node.func.id
        else:
            qualname = ast.unparse(node.func)  # type: ignore[arg-type]

        if qualname in self.forbidden_calls:
            self._record(f"Forbidden call detected: {qualname}")
        self.generic_visit(node)

    def visit_Exec(self, node: ast.Exec) -> None:  # pragma: no cover - Python <3
        self._record("exec statements are forbidden")

    def visit_Global(self, node: ast.Global) -> None:
        for name in node.names:
            if name.upper().endswith("TOKEN"):
                self._record("Global secret token variables are not allowed")
        self.generic_visit(node)


def load_source_ast(path: Path) -> ast.AST:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as fh:
        source = fh.read()
    return ast.parse(source, filename=str(path))


def analyze_source(tree: ast.AST, constitution: dict) -> None:
    visitor = _LawVisitor(constitution)
    visitor.visit(tree)
    if visitor.errors:
        raise ValueError("; ".join(visitor.errors))


def check_proposal(paths: Iterable[Path], constitution: dict | None = None) -> ValidationResult:
    constitution = constitution or {}
    errors: List[str] = []
    for path in paths:
        try:
            tree = load_source_ast(path)
            analyze_source(tree, constitution)
        except Exception as exc:  # broad capture for reporting
            errors.append(f"{path}: {exc}")
    return ValidationResult(errors=errors)


__all__ = [
    "ValidationResult",
    "check_proposal",
    "load_source_ast",
    "analyze_source",
]
