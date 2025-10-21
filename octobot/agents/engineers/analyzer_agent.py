"""Repository scanning agent."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from octobot.laws.validator import enforce, guard, register_agent
from octobot.memory.logger import log_event
from octobot.memory.reporter import AnalyzerSummary, Reporter
from octobot.memory.utils import proposals_root, timestamp


@dataclass
class AnalyzerFinding:
    file_path: str
    issue_type: str
    detail: str


register_agent("analyzer")


class AnalyzerAgent:
    """Perform static analysis over the repository tree."""

    def __init__(self, repo_root: Path | None = None, reporter: Reporter | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.reporter = reporter or Reporter()

    @guard("analyzer")
    def scan_repo(self) -> Dict[str, object]:
        """Return a structured analysis of the repository."""
        enforce("filesystem_write", str(proposals_root()))
        python_files = list(self._iter_python_files())
        findings: List[AnalyzerFinding] = []
        todos = 0
        missing_docstrings = 0
        total_complexity = 0
        for path in python_files:
            source = path.read_text(encoding="utf-8")
            todos += source.count("TODO")
            tree = ast.parse(source, filename=str(path))
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
        enforce("filesystem_write", str(report_path))
        workspace.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    def _iter_python_files(self) -> Iterable[Path]:
        for path in self.repo_root.rglob("*.py"):
            if "__pycache__" in path.parts or path.parts[0] in {"venv", ".git"}:
                continue
            yield path

    def _analyse_module(self, path: Path, tree: ast.AST) -> tuple[List[AnalyzerFinding], int, int]:
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
            except (ValueError, TypeError):
                return 0.0
        return 0.0
