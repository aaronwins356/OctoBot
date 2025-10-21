"""Executive orchestrator coordinating tasks across modules."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from orchestrator.evaluator import Evaluator, EvaluationResult
from orchestrator.task_planner import TaskPlanner
from reasoning.local_llm_client import LocalLLMClient
from reasoning.reflection_engine import ReflectionEngine
from safety.audit_log import AuditLogger
from safety.rules import SafetyRules
from memory.recall import MemoryRecall


@dataclass
class OrchestratorConfig:
    """Configuration for the executive orchestrator."""

    evaluation_threshold: float
    max_depth: int


@dataclass
class ExecutiveOrchestrator:
    """Meta-controller that decomposes goals and routes tasks."""

    config: OrchestratorConfig
    planner: TaskPlanner = field(init=False)
    evaluator: Evaluator = field(init=False)
    llm_client: LocalLLMClient = field(default_factory=LocalLLMClient)
    memory: MemoryRecall = field(default_factory=MemoryRecall)
    reflection: ReflectionEngine = field(default_factory=ReflectionEngine)
    audit_logger: AuditLogger = field(default_factory=AuditLogger)
    safety_rules: SafetyRules = field(default_factory=SafetyRules)

    def __post_init__(self) -> None:
        self.planner = TaskPlanner(max_depth=self.config.max_depth)
        self.evaluator = Evaluator(threshold=self.config.evaluation_threshold)

    def execute_goal(self, goal: str) -> Dict[str, object]:
        """Execute a goal by planning, reasoning, and reflecting."""

        self.audit_logger.log_event("goal_received", {"goal": goal})
        plan = self.planner.create_plan(goal)
        task_results: List[EvaluationResult] = []
        for task in plan.tasks:
            if task.parent_id is None:
                continue
            if not self.safety_rules.is_task_allowed(task.description):
                self.audit_logger.log_event("task_blocked", {"task": task.description})
                continue
            context = self.memory.recall(task.description)
            prompt = self._compose_prompt(task.description, context)
            response = self.llm_client.generate(prompt)
            evaluation = self.evaluator.rank([response], reference=task.description)[0]
            task_results.append(evaluation)
            self.memory.store(task.description, response)
            self.audit_logger.log_event(
                "task_completed",
                {"task": task.description, "score": evaluation.score, "response": response},
            )

        insights = self.reflection.reflect(plan.goal, task_results)
        self.memory.store_insight(plan.goal, insights)
        self.audit_logger.log_event("goal_completed", {"goal": goal, "insights": insights})
        return {
            "plan": plan,
            "results": task_results,
            "insights": insights,
        }

    @staticmethod
    def _compose_prompt(task_description: str, context: Optional[str]) -> str:
        """Compose a prompt for the reasoning module using retrieved context."""

        if context:
            return f"Task: {task_description}\nRelevant context: {context}\nAnswer:"
        return f"Task: {task_description}\nAnswer:"
