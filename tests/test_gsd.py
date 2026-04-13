"""
Tests for GSDTaskGraph (US-014)
"""

import pytest
import json
from pathlib import Path

from slimzero.agent.gsd import GSDTaskGraph, GSDTask, TaskStatus


class TestGSDTask:
    """Tests for GSDTask class."""

    def test_task_creation(self):
        """Test task creation."""
        task = GSDTask(task_id="t1", description="Test task")
        assert task.task_id == "t1"
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING

    def test_task_with_dependencies(self):
        """Test task with dependencies."""
        task = GSDTask(task_id="t1", description="Test", dependencies=["t0"])
        assert "t0" in task.dependencies

    def test_task_to_dict(self):
        """Test task serialization."""
        task = GSDTask(task_id="t1", description="Test")
        data = task.to_dict()
        assert data["task_id"] == "t1"
        assert data["status"] == "pending"

    def test_task_from_dict(self):
        """Test task deserialization."""
        data = {"task_id": "t1", "description": "Test", "status": "completed"}
        task = GSDTask.from_dict(data)
        assert task.task_id == "t1"
        assert task.status == TaskStatus.COMPLETED


class TestGSDTaskGraph:
    """Tests for GSDTaskGraph class."""

    def test_graph_creation(self):
        """Test graph creation."""
        graph = GSDTaskGraph(goal="Test goal")
        assert graph.goal == "Test goal"
        assert len(graph._tasks) == 0

    def test_add_task(self):
        """Test adding tasks."""
        graph = GSDTaskGraph(goal="Test goal")
        task = GSDTask(task_id="t1", description="Task 1")
        graph.add_task(task)
        assert "t1" in graph._tasks

    def test_add_task_with_deps(self):
        """Test adding task with dependencies."""
        graph = GSDTaskGraph(goal="Test goal")
        t1 = GSDTask(task_id="t1", description="Task 1")
        t2 = GSDTask(task_id="t2", description="Task 2", dependencies=["t1"])
        graph.add_task(t1)
        graph.add_task(t2)
        assert t2.dependencies == ["t1"]

    def test_validate_valid_decomposition(self):
        """Test validation of valid decomposition."""
        graph = GSDTaskGraph(goal="Test")
        data = [
            {"task_id": "t1", "description": "Task 1"},
            {"task_id": "t2", "description": "Task 2", "dependencies": ["t1"]},
        ]
        assert graph._is_valid_decomposition(data) is True

    def test_validate_invalid_decomposition(self):
        """Test validation of invalid decomposition."""
        graph = GSDTaskGraph(goal="Test")
        assert graph._is_valid_decomposition("not a list") is False
        assert graph._is_valid_decomposition([{"description": "No ID"}]) is False

    def test_decompose_valid_json(self):
        """Test decomposing valid JSON."""
        graph = GSDTaskGraph(goal="Test goal")
        json_str = '[{"task_id": "t1", "description": "Task 1"}, {"task_id": "t2", "description": "Task 2", "dependencies": ["t1"]}]'
        result = graph.decompose(json_str)
        assert result is True
        assert len(graph._tasks) == 2

    def test_decompose_invalid_json(self):
        """Test decomposing invalid JSON."""
        graph = GSDTaskGraph(goal="Test goal")
        result = graph.decompose("not json")
        assert result is False

    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        graph = GSDTaskGraph(goal="Test")
        t1 = GSDTask(task_id="t1", description="Task 1")
        t2 = GSDTask(task_id="t2", description="Task 2", dependencies=["t1"])
        graph.add_task(t1)
        graph.add_task(t2)

        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "t1"

    def test_update_task_status(self):
        """Test updating task status."""
        graph = GSDTaskGraph(goal="Test")
        task = GSDTask(task_id="t1", description="Task 1")
        graph.add_task(task)

        graph.update_task_status("t1", TaskStatus.COMPLETED, output="result")
        assert graph._tasks["t1"].status == TaskStatus.COMPLETED
        assert graph._tasks["t1"].output == "result"

    def test_get_pending_count(self):
        """Test pending count."""
        graph = GSDTaskGraph(goal="Test")
        graph.add_task(GSDTask(task_id="t1", description="Task 1"))
        graph.add_task(GSDTask(task_id="t2", description="Task 2"))
        assert graph.get_pending_count() == 2

    def test_get_completed_count(self):
        """Test completed count."""
        graph = GSDTaskGraph(goal="Test")
        t1 = GSDTask(task_id="t1", description="Task 1")
        t2 = GSDTask(task_id="t2", description="Task 2")
        graph.add_task(t1)
        graph.add_task(t2)
        graph.update_task_status("t1", TaskStatus.COMPLETED)
        assert graph.get_completed_count() == 1

    def test_is_complete(self):
        """Test is_complete check."""
        graph = GSDTaskGraph(goal="Test")
        t1 = GSDTask(task_id="t1", description="Task 1")
        graph.add_task(t1)
        assert graph.is_complete() is False
        graph.update_task_status("t1", TaskStatus.COMPLETED)
        assert graph.is_complete() is True

    def test_to_dict(self):
        """Test export to dict."""
        graph = GSDTaskGraph(goal="Test goal")
        graph.add_task(GSDTask(task_id="t1", description="Task 1"))
        data = graph.to_dict()
        assert data["goal"] == "Test goal"
        assert len(data["tasks"]) == 1
