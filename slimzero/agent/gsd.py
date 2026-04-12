"""
SlimZero GSD Task Graph (US-014)

Task decomposition layer using networkx DiGraph.
Breaks goals into checkpointed sub-tasks with dependency management.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

from slimzero.exceptions import SlimZeroError

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not available. GSD task graph will use fallback.")


class TaskStatus(Enum):
    """Status of a task node."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GSDTask:
    """Represents a single task node in the graph."""

    def __init__(
        self,
        task_id: str,
        description: str,
        dependencies: Optional[List[str]] = None,
    ):
        self.task_id = task_id
        self.description = description
        self.status = TaskStatus.PENDING
        self.dependencies = dependencies or []
        self.retry_count = 0
        self.output: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "output": str(self.output) if self.output else None,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GSDTask":
        """Create from dictionary."""
        task = cls(
            task_id=data["task_id"],
            description=data["description"],
            dependencies=data.get("dependencies", []),
        )
        task.status = TaskStatus(data.get("status", "pending"))
        task.retry_count = data.get("retry_count", 0)
        task.output = data.get("output")
        task.error = data.get("error")
        task.created_at = data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        task.completed_at = data.get("completed_at")
        return task


class GSDTaskGraph:
    """
    Task decomposition graph using networkx DiGraph.

    Each node represents a task with dependencies.
    Tasks run only when all dependencies complete.
    Checkpointed to JSON for resume capability.
    """

    def __init__(
        self,
        goal: str,
        checkpoint_dir: Optional[str] = None,
        max_retries: int = 3,
    ):
        """
        Initialize GSD Task Graph.

        Args:
            goal: The main goal to decompose.
            checkpoint_dir: Directory for checkpoint files.
            max_retries: Maximum retry attempts per task.
        """
        self.goal = goal
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path(".gsd")
        self.max_retries = max_retries

        if NETWORKX_AVAILABLE:
            self._graph = nx.DiGraph()
        else:
            self._graph = None
            self._fallback_tasks: Dict[str, GSDTask] = {}

        self._tasks: Dict[str, GSDTask] = {}
        goal_hash = hashlib.sha256(goal.encode()).hexdigest()[:16]
        self._checkpoint_path = self.checkpoint_dir / f"gsd_{goal_hash}.json"

    def _ensure_checkpoint_dir(self) -> None:
        """Ensure checkpoint directory exists."""
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def add_task(self, task: GSDTask) -> None:
        """
        Add a task to the graph.

        Args:
            task: GSDTask to add.
        """
        self._tasks[task.task_id] = task

        if self._graph is not None:
            self._graph.add_node(task.task_id)
            for dep in task.dependencies:
                self._graph.add_edge(dep, task.task_id)
        else:
            self._fallback_tasks[task.task_id] = task

    def _validate_no_circular_dependencies(self) -> bool:
        """Validate graph has no circular dependencies."""
        if self._graph is None:
            return True

        try:
            nx.find_cycle(self._graph)
            return False
        except nx.NetworkXNoCycle:
            return True

    def _is_valid_decomposition(self, tasks: List[Dict[str, Any]]) -> bool:
        """Validate task decomposition JSON."""
        if not isinstance(tasks, list):
            return False

        task_ids = set()
        for task in tasks:
            if not isinstance(task, dict):
                return False
            if "task_id" not in task or "description" not in task:
                return False
            if task["task_id"] in task_ids:
                return False
            task_ids.add(task["task_id"])

        return True

    def decompose(self, decomposition_json: str) -> bool:
        """
        Load task decomposition from JSON.

        Args:
            decomposition_json: JSON string with task decomposition.

        Returns:
            True if valid, False otherwise.
        """
        try:
            data = json.loads(decomposition_json)
            if not self._is_valid_decomposition(data):
                logger.error("Invalid task decomposition format")
                return False

            for task_data in data:
                task = GSDTask(
                    task_id=task_data["task_id"],
                    description=task_data["description"],
                    dependencies=task_data.get("dependencies", []),
                )
                self.add_task(task)

            if not self._validate_no_circular_dependencies():
                logger.error("Circular dependencies detected")
                return False

            self._ensure_checkpoint_dir()
            self._save_checkpoint()
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return False

    def get_ready_tasks(self) -> List[GSDTask]:
        """Get tasks that are ready to run (all dependencies completed)."""
        ready = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue

            deps_completed = all(
                self._tasks[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
                if dep in self._tasks
            )

            if deps_completed:
                ready.append(task)

        return ready

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        output: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update task status.

        Args:
            task_id: ID of task to update.
            status: New status.
            output: Task output (if completed).
            error: Error message (if failed).
        """
        if task_id not in self._tasks:
            logger.warning(f"Unknown task: {task_id}")
            return

        task = self._tasks[task_id]
        task.status = status
        task.output = output
        task.error = error

        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        if status == TaskStatus.FAILED:
            task.retry_count += 1

        self._save_checkpoint()

    def _save_checkpoint(self) -> None:
        """Save checkpoint to JSON."""
        self._ensure_checkpoint_dir()

        checkpoint_data = {
            "goal": self.goal,
            "checkpoint_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tasks": {tid: task.to_dict() for tid, task in self._tasks.items()},
        }

        with open(self._checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2)

        logger.info(f"Checkpoint saved: {self._checkpoint_path}")

    def load_checkpoint(self) -> bool:
        """
        Load checkpoint from file.

        Returns:
            True if checkpoint loaded, False if none exists.
        """
        if not self._checkpoint_path.exists():
            return False

        try:
            with open(self._checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._tasks = {
                tid: GSDTask.from_dict(tdata)
                for tid, tdata in data.get("tasks", {}).items()
            }

            if self._graph is not None:
                self._graph = nx.DiGraph()
                for task in self._tasks.values():
                    self._graph.add_node(task.task_id)
                    for dep in task.dependencies:
                        self._graph.add_edge(dep, task.task_id)

            logger.info(f"Checkpoint loaded: {self._checkpoint_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False

    def get_pending_count(self) -> int:
        """Get count of pending tasks."""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

    def get_completed_count(self) -> int:
        """Get count of completed tasks."""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)

    def is_complete(self) -> bool:
        """Check if all tasks are complete."""
        if not self._tasks:
            return False
        return all(t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for t in self._tasks.values())

    def to_dict(self) -> Dict[str, Any]:
        """Export graph state as dictionary."""
        return {
            "goal": self.goal,
            "tasks": {tid: task.to_dict() for tid, task in self._tasks.items()},
            "pending_count": self.get_pending_count(),
            "completed_count": self.get_completed_count(),
            "is_complete": self.is_complete(),
        }
