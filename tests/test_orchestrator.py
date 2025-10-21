"""End-to-end test for orchestrator execution."""
from pathlib import Path

from orchestrator.main_controller import ExecutiveOrchestrator, OrchestratorConfig
from memory.recall import MemoryRecall
from reasoning.local_llm_client import LocalLLMClient
from reasoning.reflection_engine import ReflectionEngine
from safety.audit_log import AuditLogger
from safety.rules import SafetyRules


def test_execute_goal_produces_insights(tmp_path: Path) -> None:
    memory = MemoryRecall(database_path=str(tmp_path / "brain.db"), embedding_dim=16)
    orchestrator = ExecutiveOrchestrator(
        config=OrchestratorConfig(evaluation_threshold=0.1, max_depth=2),
        llm_client=LocalLLMClient(use_stub=True),
        memory=memory,
        reflection=ReflectionEngine(),
        audit_logger=AuditLogger(log_path=tmp_path / "audit.log"),
        safety_rules=SafetyRules(),
    )
    result = orchestrator.execute_goal("Document the API endpoints and summarize outputs.")
    assert result["insights"].startswith("Reflection")
    assert result["plan"].goal.startswith("Document the API")
    assert result["results"]
