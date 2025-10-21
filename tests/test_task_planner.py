"""Tests for the task planner."""
from orchestrator.task_planner import TaskPlanner


def test_create_plan_creates_subtasks() -> None:
    planner = TaskPlanner(max_depth=2)
    plan = planner.create_plan("Draft the research plan, review data sources.")
    assert plan.goal == "Draft the research plan, review data sources."
    # Root plus two subtasks (limited by max_depth)
    assert len(plan.tasks) == 3
    assert plan.subtasks_for("task-0")
