"""Task planning utilities for The Brain orchestrator."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TaskNode:
    """Represents a single task within a plan."""

    task_id: str
    description: str
    parent_id: Optional[str] = None
    status: str = "pending"
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Return a serialisable representation of the task node."""

        return {
            "task_id": self.task_id,
            "description": self.description,
            "parent_id": self.parent_id,
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass
class TaskPlan:
    """Structured plan that captures a hierarchy of tasks."""

    goal: str
    tasks: List[TaskNode]

    def subtasks_for(self, task_id: str) -> List[TaskNode]:
        """Return subtasks for a given task identifier."""

        return [task for task in self.tasks if task.parent_id == task_id]

    def root_tasks(self) -> List[TaskNode]:
        """Return the top-level tasks for the plan."""

        return [task for task in self.tasks if task.parent_id is None]

    def to_dict(self) -> Dict[str, object]:
        """Return a serialisable form of the plan."""

        return {
            "goal": self.goal,
            "tasks": [task.to_dict() for task in self.tasks],
        }


@dataclass
class TaskPlanner:
    """Creates hierarchical task plans from free-form goals."""

    max_depth: int = 3

    def create_plan(self, goal: str) -> TaskPlan:
        """Generate a task plan by decomposing the provided goal."""

        normalized_goal = goal.strip()
        if not normalized_goal:
            raise ValueError("Goal must be a non-empty string.")

        root_task = TaskNode(task_id="task-0", description=normalized_goal)
        subtasks = self._infer_subtasks(root_task)
        tasks = [root_task, *subtasks]
        return TaskPlan(goal=normalized_goal, tasks=tasks)

    def _infer_subtasks(self, root_task: TaskNode) -> List[TaskNode]:
        """Infer subtasks heuristically based on the root task description."""

        clauses = self._split_into_clauses(root_task.description)
        subtasks: List[TaskNode] = []
        for index, clause in enumerate(clauses[: self.max_depth]):
            task_id = f"task-0-{index + 1}"
            subtasks.append(
                TaskNode(
                    task_id=task_id,
                    description=clause,
                    parent_id=root_task.task_id,
                    metadata={"priority": str(index + 1)},
                )
            )
        return subtasks

    @staticmethod
    def _split_into_clauses(text: str) -> List[str]:
        """Split the goal text into clause-like segments for task generation."""

        fragments = [fragment.strip() for fragment in re.split(r"[.;,:]+", text) if fragment.strip()]
        if not fragments:
            fragments = [text.strip()]
        return fragments


def flatten_tasks(plan: TaskPlan) -> List[TaskNode]:
    """Return a flat list of tasks from the plan (utility for tests)."""

    return list(plan.tasks)
