from __future__ import annotations

from pathlib import Path

from octobot.agents.engineers.analyzer_agent import AnalyzerAgent


def _create_file(path: Path, content: str = "print('ok')\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_analyzer_skips_virtualenv_and_git(tmp_path: Path) -> None:
    _create_file(tmp_path / "src" / "main.py")
    _create_file(tmp_path / ".venv" / "lib" / "site.py")
    _create_file(tmp_path / ".git" / "hooks" / "pre-commit")

    agent = AnalyzerAgent(repo_root=tmp_path)
    files = {path.relative_to(tmp_path).as_posix() for path in agent._iter_python_files()}

    assert files == {"src/main.py"}
