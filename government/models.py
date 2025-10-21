"""Structured message models used by the government orchestrator."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AgentRegistration(BaseModel):
    name: str
    module_path: Path
    sandbox_path: Path


class AgentExecutionResult(BaseModel):
    name: str
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    report: Dict[str, Any] = Field(default_factory=dict)
    sandbox_path: Path


class ProposalRecord(BaseModel):
    proposal_id: str
    agent: str
    path: Path
    summary: str = ""
    evaluation: Dict[str, Any] = Field(default_factory=dict)
    draft_pr_url: Optional[str] = None


__all__ = [
    "AgentRegistration",
    "AgentExecutionResult",
    "ProposalRecord",
]
