"""AST-based repository analyzer for OctoBot."""
from __future__ import annotations

import ast
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from laws.validator import DEFAULT_VALIDATOR
from memory.history_logger import HistoryLogger
from memory.reporter import AnalyzerSummary, Reporter


@dataclass
class AnalyzerFinding:
    file_path: str
    issue_type: str
    detail: str


class AnalyzerAgent:
    def __init__(self, repo_root: Path | None = None, reporter: Reporter | None = None, logger: HistoryLogger | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.reporter = reporter or Reporter()
        self.logger = logger or HistoryLogger()

    def scan_repo(self) -> Dict[str, List[Dict[str, str]]]:
        DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
        python_files = list(self._iter_python_files())
        findings: List[AnalyzerFinding] = []
        unused_imports = 0
        missing_docstrings = 0
        for path in python_files:
            module = path.read_text(encoding="utf-8")
            tree = ast.parse(module, filename=str(path))
            findings.extend(self._analyze_module(path, tree))
            unused_imports += self._count_unused_imports(tree)
            missing_docstrings += self._count_missing_docstrings(tree)
        findings_dicts = [finding.__dict__ for finding in findings]
        self.reporter.record_analyzer_summary(
            AnalyzerSummary(
                files_scanned=len(python_files),
                functions_flagged=sum(1 for f in findings if f.issue_type == "complexity"),
                unused_imports=unused_imports,
                missing_docstrings=missing_docstrings,
            )
        )
        report = {
            "findings": findings_dicts,
            "files_scanned": len(python_files),
            "unused_imports": unused_imports,
            "missing_docstrings": missing_docstrings,
        }
        self.logger.log_event(
            f"Analyzer scanned {len(python_files)} files and recorded {len(findings_dicts)} findings"
        )
        (self.repo_root / "reports").mkdir(exist_ok=True)
        report_path = self.repo_root / "reports" / "analyzer_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    def _iter_python_files(self) -> Iterable[Path]:
        for path in self.repo_root.rglob("*.py"):
            if any(part.startswith(".") for part in path.parts):
                continue
            if "__pycache__" in path.parts or path.parts[0] == "venv":
                continue
            yield path

    def _analyze_module(self, path: Path, tree: ast.AST) -> List[AnalyzerFinding]:
        findings: List[AnalyzerFinding] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._cyclomatic_complexity(node)
                if complexity > 10:
                    findings.append(
                        AnalyzerFinding(
                            file_path=str(path.relative_to(self.repo_root)),
                            issue_type="complexity",
                            detail=f"Function {node.name} has cyclomatic complexity {complexity}",
                        )
                    )
        duplicate_counts = Counter()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                duplicate_counts[node.func.id] += 1
        for name, count in duplicate_counts.items():
            if count > 5:
                findings.append(
                    AnalyzerFinding(
                        file_path=str(path.relative_to(self.repo_root)),
                        issue_type="repetition",
                        detail=f"Function name {name} appears {count} times",
                    )
                )
        return findings

    def _cyclomatic_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp, ast.Match)):
                complexity += 1
        return complexity

    def _count_unused_imports(self, tree: ast.AST) -> int:
        imported_names = set()
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        return len(imported_names - used_names)

    def _count_missing_docstrings(self, tree: ast.AST) -> int:
        count = 0
        for node in tree.body if isinstance(tree, ast.Module) else []:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    count += 1
        return count
