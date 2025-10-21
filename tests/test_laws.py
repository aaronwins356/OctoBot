"""Tests for law enforcement and validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from laws.enforcement import LawViolation, verify_agent_code


def test_verify_agent_code_rejects_dangerous_calls() -> None:
    agent_dir = Path("entrepreneurs")
    bad_file = agent_dir / "malicious_agent.py"
    bad_source = """
from entrepreneurs.base_agent import BaseAgent


class MaliciousAgent(BaseAgent):
    def setup(self):
        pass

    def run(self, input_data):
        import subprocess
        subprocess.Popen('rm -rf /')

    def report(self):
        return {}
"""
    bad_file.write_text(bad_source, encoding="utf-8")
    try:
        with pytest.raises((LawViolation, ValueError)):
            verify_agent_code(bad_file)
    finally:
        bad_file.unlink(missing_ok=True)


def test_verify_agent_code_accepts_writer_agent() -> None:
    writer_path = Path("entrepreneurs/writer_agent.py")
    verify_agent_code(writer_path)
