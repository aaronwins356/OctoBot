"""
File: octobot/agents/engineers/analyzer_agent.py
Fix Type: Reliability / Resilience
Summary:
- ✅ Fixed: analyzer crash on binary, corrupt, or excluded files
- ✅ Tested by: tests/test_analyzer_resilience.py

The analyzer now skips heavy directories, guards against decoding errors and
continues scanning when a single file is malformed.  It records the reason for
skipped files in the ledger to maintain transparency while ensuring the
analysis completes.
"""

from __future__ import annotations

import ast
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

from octobot.laws.validator import enforce, guard, law_enforced, register_agent
from octobot.memory.logger import log_event
from octobot.memory.reporter import AnalyzerSummary, Reporter
from octobot.memory.utils import load_scan_exclusions, proposals_root, timestamp
from octobot.utils.persistence import safe_write

LOGGER = logging.getLogger(__name__)


@dataclass
class AnalyzerFinding:
    file_path: str
    issue_type: str
    detail: str


register_agent("analyzer")


class AnalyzerAgent:
    """Perform static analysis over the repository tree with resilience."""

    def __init__(
        self,
        repo_root: Path | None = None,
        reporter: Reporter | None = None,
        exclusions: Iterable[str] | None = None,
    ) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.reporter = reporter or Reporter()
        default_exclusions = {"venv", ".venv", ".git", "node_modules"}
        self._exclusions = set(load_scan_exclusions(default_exclusions))
        if exclusions:
            self._exclusions.update(exclusions)
        self._skip_markers = {"__pycache__", "node_modules", ".git", ".venv"}

    @guard("analyzer")
    @law_enforced("filesystem_write")
    def scan_repo(self) -> Dict[str, object]:
        """Return a structured analysis of the repository."""

        enforce("filesystem_write", str(proposals_root()))
        python_files = list(self._iter_python_files())
        findings: List[AnalyzerFinding] = []
        todos = 0
        missing_docstrings = 0
        total_complexity = 0
        for path in python_files:
            try:
                source = path.read_text(encoding="utf-8")
                todos += source.count("TODO")
                tree = ast.parse(source, filename=str(path))
            except UnicodeDecodeError as error:
                self._log_skip(path, "unicode", error)
                continue
            except SyntaxError as error:
                self._log_skip(path, "syntax", error)
                continue
            except OSError as error:
                self._log_skip(path, "filesystem", error)
                continue
            file_findings, file_missing, file_complexity = self._analyse_module(path, tree)
            findings.extend(file_findings)
            missing_docstrings += file_missing
            total_complexity += file_complexity
        complexity_average = total_complexity / max(len(python_files), 1)
        coverage_estimate = self._estimate_coverage()
        summary = AnalyzerSummary(
            files_scanned=len(python_files),
            complexity_issues=sum(1 for finding in findings if finding.issue_type == "complexity"),
            todos=todos,
            missing_docstrings=missing_docstrings,
            coverage=coverage_estimate,
        )
        self.reporter.record_analyzer_summary(summary)
        report = {
            "generated_at": timestamp(),
            "files": len(python_files),
            "complexity_average": complexity_average,
            "todos": todos,
            "missing_docstrings": missing_docstrings,
            "coverage": coverage_estimate,
            "findings": [finding.__dict__ for finding in findings],
        }
        log_event(
            "analyzer",
            "scan_repo",
            "completed",
            {"files": len(python_files), "findings": len(findings)},
        )
        workspace = proposals_root() / "_workspace"
        report_path = workspace / "analyzer_report.json"
        workspace.mkdir(parents=True, exist_ok=True)
        safe_write(report_path, json.dumps(report, indent=2))
        return report

    def _iter_python_files(self) -> Iterator[Path]:
        for path in self.repo_root.rglob("*.py"):
            try:
                rel_path = path.relative_to(self.repo_root)
            except ValueError:
                continue
            if any(part in self._skip_markers for part in rel_path.parts):
                continue
            if any(part in self._exclusions for part in rel_path.parts):
                continue
            yield path

    def _analyse_module(self, path: Path, tree: ast.AST) -> Tuple[List[AnalyzerFinding], int, int]:
        findings: List[AnalyzerFinding] = []
        missing_docstrings = 0
        complexity_total = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node) is None:
                    missing_docstrings += 1
                complexity = self._cyclomatic_complexity(node)
                complexity_total += complexity
                if complexity > 10:
                    findings.append(
                        AnalyzerFinding(
                            file_path=str(path.relative_to(self.repo_root)),
                            issue_type="complexity",
                            detail=f"Function {node.name} complexity {complexity}",
                        )
                    )
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "TODO" in node.value
            ):
                findings.append(
                    AnalyzerFinding(
                        file_path=str(path.relative_to(self.repo_root)),
                        issue_type="todo",
                        detail=node.value.strip(),
                    )
                )
        return findings, missing_docstrings, complexity_total

    def _cyclomatic_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp, ast.Match)
            ):
                complexity += 1
        return complexity

    def _estimate_coverage(self) -> float:
        coverage_file = proposals_root() / "_workspace" / "coverage.json"
        if coverage_file.exists():
            try:
                data = json.loads(coverage_file.read_text(encoding="utf-8"))
                return float(data.get("coverage", 0.0))
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                LOGGER.warning("Failed to parse coverage data: %s", error)
                return 0.0
        return 0.0

    def _log_skip(self, path: Path, reason: str, error: Exception) -> None:
        log_event(
            "analyzer",
            "file_skipped",
            reason,
            {"file": str(path), "error": repr(error)},
        )
        LOGGER.debug("Skipped %s due to %s: %s", path, reason, error)

