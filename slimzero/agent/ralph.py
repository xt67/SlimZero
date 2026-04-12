"""
SlimZero Ralph Agent Loop (US-015)

Autonomous agent loop with circuit breakers and semantic drift detection.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, AnyStr

from slimzero.agent.gsd import GSDTaskGraph, TaskStatus
from slimzero.exceptions import (
    SlimZeroAgentError,
    SlimZeroCircuitBreaker,
    SlimZeroDriftHalt,
    SlimZeroToolValidationError,
    SlimZeroHumanEscalation,
)

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False


class ActionType(Enum):
    """Type of agent action."""

    THINK = "think"
    TOOL_CALL = "tool_call"
    RESPOND = "respond"
    REGROUND = "reground"


class ToolValidator:
    """Validates tool calls before execution."""

    def __init__(self):
        """Initialize validator."""
        self._known_tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a tool schema."""
        self._known_tools[name] = schema

    def validate(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a tool call.

        Args:
            tool_name: Name of tool to validate.
            arguments: Tool arguments.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if tool_name not in self._known_tools:
            return False, f"Unknown tool: {tool_name}"

        schema = self._known_tools[tool_name]
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for req in required:
            if req not in arguments:
                return False, f"Missing required argument: {req}"

        for arg_name, arg_value in arguments.items():
            if arg_name not in properties:
                return False, f"Unknown argument: {arg_name}"

        return True, None


class ActionAuditor:
    """Audits all agent actions."""

    def __init__(self):
        """Initialize auditor."""
        self._audit_log: List[Dict[str, Any]] = []

    def log(
        self,
        action_type: ActionType,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        result_summary: Optional[str] = None,
        tokens_used: int = 0,
        step: int = 0,
    ) -> None:
        """Log an action."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_type": action_type.value,
            "step": step,
            "tool_name": tool_name,
            "arguments": arguments,
            "result_summary": result_summary,
            "tokens_used": tokens_used,
        }
        self._audit_log.append(entry)
        logger.debug(f"Action logged: {action_type.value} step {step}")

    def get_log(self) -> List[Dict[str, Any]]:
        """Get audit log."""
        return self._audit_log.copy()

    def export_log(self) -> str:
        """Export audit log as JSON."""
        return json.dumps(self._audit_log, indent=2)


class RalphLoop:
    """
    Ralph autonomous agent loop with SlimZero enhancements.

    Features:
    - Circuit breaker: max_steps, max_retries, max_total_tokens
    - Semantic drift detector
    - Tool-call validator
    - Action auditor
    - Checkpointing for human escalation
    """

    def __init__(
        self,
        max_steps: int = 20,
        max_retries_per_step: int = 3,
        max_total_tokens: Optional[int] = None,
        drift_threshold: float = 0.75,
        api_client: Optional[Any] = None,
        checkpoint_dir: str = ".gsd",
    ):
        """
        Initialize Ralph Loop.

        Args:
            max_steps: Maximum steps before circuit breaker (default 20).
            max_retries_per_step: Max retries per step (default 3).
            max_total_tokens: Max total tokens before halt.
            drift_threshold: Semantic similarity threshold for drift detection.
            api_client: LLM API client.
            checkpoint_dir: Directory for checkpoints.
        """
        self.max_steps = max_steps
        self.max_retries_per_step = max_retries_per_step
        self.max_total_tokens = max_total_tokens
        self.drift_threshold = drift_threshold
        self.api_client = api_client
        self.checkpoint_dir = checkpoint_dir

        self._tool_validator = ToolValidator()
        self._auditor = ActionAuditor()
        self._drift_detector = None
        self._task_graph: Optional[GSDTaskGraph] = None

        self._step_count = 0
        self._total_tokens = 0
        self._consecutive_drift_count = 0
        self._current_goal: Optional[str] = None
        self._original_plan: Optional[str] = None

        if ST_AVAILABLE:
            try:
                self._drift_detector = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Failed to load drift detector: {e}")

    def register_tool(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a tool for validation."""
        self._tool_validator.register_tool(name, schema)

    def _check_circuit_breaker(self) -> None:
        """Check and raise circuit breaker if needed."""
        if self._step_count >= self.max_steps:
            raise SlimZeroCircuitBreaker(
                "Max steps exceeded",
                reason="max_steps",
                steps_taken=self._step_count,
            )

        if self.max_total_tokens and self._total_tokens >= self.max_total_tokens:
            raise SlimZeroCircuitBreaker(
                "Max tokens exceeded",
                reason="max_tokens",
                steps_taken=self._step_count,
            )

    def _detect_drift(self, current_plan: str) -> bool:
        """Detect semantic drift from original plan."""
        if not self._drift_detector or not self._original_plan:
            return False

        try:
            embeddings = self._drift_detector.encode([self._original_plan, current_plan])
            emb1, emb2 = embeddings[0], embeddings[1]

            dot = sum(a * b for a, b in zip(emb1, emb2))
            norm1 = sum(a * a for a in emb1) ** 0.5
            norm2 = sum(a * a for a in emb2) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return False

            similarity = dot / (norm1 * norm2)

            if similarity < self.drift_threshold:
                self._consecutive_drift_count += 1
                if self._consecutive_drift_count >= 3:
                    raise SlimZeroDriftHalt(
                        "Semantic drift detected",
                        drift_similarity=similarity,
                        threshold=self.drift_threshold,
                    )
                return True

            self._consecutive_drift_count = 0
            return False

        except SlimZeroDriftHalt:
            raise
        except Exception as e:
            logger.warning(f"Drift detection failed: {e}")
            return False

    def _validate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Validate a tool call."""
        is_valid, error = self._tool_validator.validate(tool_name, arguments)
        if not is_valid:
            raise SlimZeroToolValidationError(
                error or "Tool validation failed",
                tool_name=tool_name,
                validation_errors=[error] if error else [],
            )

    def _checkpoint_state(self) -> str:
        """Save checkpoint before escalation."""
        import os
        checkpoint_path = os.path.join(self.checkpoint_dir, "ralph_checkpoint.json")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        checkpoint_data = {
            "goal": self._current_goal,
            "original_plan": self._original_plan,
            "step_count": self._step_count,
            "total_tokens": self._total_tokens,
            "audit_log": self._auditor.get_log(),
        }

        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2)

        return checkpoint_path

    def run(
        self,
        goal: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        initial_plan: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the agent loop.

        Args:
            goal: The goal to accomplish.
            tools: List of available tools.
            initial_plan: Optional initial plan.

        Returns:
            Dict with result and audit trail.
        """
        self._current_goal = goal
        self._original_plan = initial_plan or goal
        self._step_count = 0
        self._total_tokens = 0
        self._consecutive_drift_count = 0

        if tools:
            for tool in tools:
                if "name" in tool and "parameters" in tool:
                    self.register_tool(tool["name"], tool["parameters"])

        self._auditor.log(ActionType.THINK, step=0)
        logger.info(f"Starting Ralph loop for goal: {goal[:50]}...")

        try:
            while self._step_count < self.max_steps:
                self._step_count += 1
                self._check_circuit_breaker()

                step_result = self._execute_step(goal)
                self._auditor.log(
                    ActionType.RESPOND,
                    result_summary=str(step_result)[:200],
                    step=self._step_count,
                )

                if step_result.get("done"):
                    break

                current_plan = step_result.get("plan", "")
                if self._detect_drift(current_plan):
                    self._auditor.log(
                        ActionType.REGROUND,
                        result_summary="Re-grounding due to drift",
                        step=self._step_count,
                    )

            return {
                "result": "max_steps_reached",
                "steps": self._step_count,
                "audit_log": self._auditor.export_log(),
            }

        except SlimZeroHumanEscalation:
            checkpoint_path = self._checkpoint_state()
            raise

        except SlimZeroCircuitBreaker as e:
            logger.warning(f"Circuit breaker: {e}")
            return {
                "result": "circuit_breaker",
                "reason": e.reason,
                "steps": self._step_count,
                "audit_log": self._auditor.export_log(),
            }

        except SlimZeroDriftHalt as e:
            logger.warning(f"Drift halt: {e}")
            return {
                "result": "drift_detected",
                "similarity": e.drift_similarity,
                "steps": self._step_count,
                "audit_log": self._auditor.export_log(),
            }

    def _execute_step(self, goal: str) -> Dict[str, Any]:
        """Execute a single step. Override for actual implementation."""
        return {"done": True, "plan": goal}

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "steps_taken": self._step_count,
            "total_tokens": self._total_tokens,
            "audit_entries": len(self._auditor.get_log()),
            "consecutive_drift": self._consecutive_drift_count,
        }
