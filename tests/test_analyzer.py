from __future__ import annotations

from pathlib import Path

from engineers.analyzer_agent import AnalyzerAgent


def test_analyzer_detects_missing_docstring(tmp_path: Path) -> None:
    module = tmp_path / "sample.py"
    module.write_text(
        "import os\n\n"
        "def complex_function(x):\n"
        "    if x > 0:\n"
        "        return x\n"
        "    else:\n"
        "        return -x\n",
        encoding="utf-8",
    )
    analyzer = AnalyzerAgent(repo_root=tmp_path)
    report = analyzer.scan_repo()
    assert report["files_scanned"] == 1
    assert report["missing_docstrings"] >= 1
