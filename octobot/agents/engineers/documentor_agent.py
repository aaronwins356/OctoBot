"""Documentation regeneration agent."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Tuple

from octobot.laws.validator import enforce, guard, register_agent
from octobot.memory.logger import log_event
from octobot.memory.utils import load_yaml, repo_root

register_agent("documentor")


class DocumentorAgent:
    """Scan docstrings and regenerate human-readable documentation."""

    def __init__(self, repo_root_path: Path | None = None) -> None:
        self.repo_root = repo_root_path or repo_root()

    @guard("documentor")
    def write_summary(self, proposal_dir: Path, context: Dict[str, str]) -> Path:
        document_path = proposal_dir / "SUMMARY.md"
        enforce("filesystem_write", str(document_path))
        topic = context.get("topic", "General maintenance")
        rationale = context.get(
            "rationale",
            "Automated suggestion based on analyzer report.",
        )
        lines = [
            "# Proposal Summary",
            "",
            f"## Topic\n{topic}",
            "",
            f"## Rationale\n{rationale}",
            "",
            "## Highlights",
            f"- Impact: {context.get('impact', 'medium')}",
            f"- Risk: {context.get('risk', 'low')}",
            "",
            "## Notes",
            "This summary is generated for human review and must be approved before publication.",
        ]
        proposal_dir.mkdir(parents=True, exist_ok=True)
        document_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log_event("documentor", "summary", "generated", document_path.as_posix())
        return document_path

    @guard("documentor")
    def rebuild_docs(self) -> None:
        docs_dir = self.repo_root / "docs"
        enforce("filesystem_write", str(docs_dir))
        docs_dir.mkdir(parents=True, exist_ok=True)
        modules = self._collect_module_docs()
        self._write_index(docs_dir, modules)
        self._write_architecture(docs_dir, modules)
        self._write_laws(docs_dir)
        self._write_developer_guide(docs_dir)
        log_event("documentor", "rebuild_docs", "completed", {"modules": len(modules)})

    def _collect_module_docs(self) -> List[Tuple[str, str]]:
        package = importlib.import_module("octobot")
        modules: List[Tuple[str, str]] = []
        for _finder, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                module = importlib.import_module(name)
            except Exception:  # pragma: no cover - defensive against optional deps
                continue
            doc = inspect.getdoc(module) or "No documentation available."
            modules.append((name, doc))
        modules.sort()
        return modules

    def _write_index(self, docs_dir: Path, modules: List[Tuple[str, str]]) -> None:
        index_path = docs_dir / "index.md"
        enforce("filesystem_write", str(index_path))
        intro = [
            "# OctoBot Documentation",
            "",
            (
                "This site is generated nightly from module docstrings "
                "to keep guidance in sync with the codebase."
            ),
            "",
            "## Module Overview",
        ]
        for name, summary in modules[:20]:
            intro.append(f"- **{name}** – {summary.splitlines()[0]}")
        index_path.write_text("\n".join(intro) + "\n", encoding="utf-8")

    def _write_architecture(self, docs_dir: Path, modules: List[Tuple[str, str]]) -> None:
        architecture_path = docs_dir / "architecture.md"
        enforce("filesystem_write", str(architecture_path))
        sections = [
            "# Architecture",
            "",
            (
                "OctoBot is organised into constitutional subsystems. "
                "The following highlights the most important modules:"
            ),
            "",
        ]
        for name, summary in modules:
            if name.count(".") > 3:
                continue
            sections.append(f"## {name}")
            sections.append("")
            sections.append(summary)
            sections.append("")
        architecture_path.write_text("\n".join(sections), encoding="utf-8")

    def _write_laws(self, docs_dir: Path) -> None:
        laws_path = docs_dir / "laws.md"
        enforce("filesystem_write", str(laws_path))
        constitution = load_yaml(self.repo_root / "octobot" / "laws" / "constitution.yaml")
        ethics = load_yaml(self.repo_root / "octobot" / "laws" / "ethics.yaml")
        tech = load_yaml(self.repo_root / "octobot" / "laws" / "tech_standards.yaml")
        lines = [
            "# Constitutional Laws",
            "",
            "## Constitution",
        ]
        for name, desc in constitution.get("rules", {}).items():
            lines.append(f"- **{name}**: {desc}")
        lines.extend(["", "## Ethics"])
        for principle in ethics.get("principles", []):
            lines.append(f"- {principle}")
        lines.extend(["", "## Technical Standards"])
        for key, value in tech.get("quality_gates", {}).items():
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        laws_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_developer_guide(self, docs_dir: Path) -> None:
        guide_path = docs_dir / "developer_guide.md"
        enforce("filesystem_write", str(guide_path))
        lines = [
            "# Developer Guide",
            "",
            "## Environment Setup",
            "1. Install Poetry 1.8+",
            "2. Run `poetry install`",
            "3. Activate pre-commit hooks with `poetry run pre-commit install`",
            "",
            "## Quality Gates",
            "- Tests must maintain >= 90% coverage",
            "- Safety scans must pass before merge",
            "",
            "## Deployment",
            "Use the provided Dockerfile which mounts `/workspace` and runs the governance CLI.",
        ]
        guide_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:  # pragma: no cover - script entrypoint
    DocumentorAgent().rebuild_docs()


if __name__ == "__main__":  # pragma: no cover
    main()
