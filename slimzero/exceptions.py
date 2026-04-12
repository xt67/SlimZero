"""
SlimZero Exception Hierarchy

All SlimZero errors inherit from SlimZeroError base class.
Fault prevention rules ensure all errors are logged before being raised.
"""

from typing import Optional, Any, Dict


class SlimZeroError(Exception):
    """Base exception for all SlimZero errors."""

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.stage = stage
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging."""
        return {
            "type": self.__class__.__name__,
            "message": str(self),
            "stage": self.stage,
            "context": self.context,
        }


class SlimZeroInputError(SlimZeroError):
    """Invalid input to pipeline (missing required fields, null prompt)."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, stage="input_validation", context=context)
        self.field_name = field_name


class SlimZeroRewriteError(SlimZeroError):
    """Rewriter produced invalid output."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, stage="prompt_rewriter", context=context)


class SlimZeroSemanticRejection(SlimZeroError):
    """
    Rewrite rejected by semantic guard.
    This is not an error - logged as INFO level.
    """

    def __init__(
        self,
        message: str,
        similarity: Optional[float] = None,
        threshold: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, stage="semantic_guard", context=context)
        self.similarity = similarity
        self.threshold = threshold


class SlimZeroBudgetWarning(SlimZeroError):
    """
    Prompt could not be brought within budget.
    Warning level - request may proceed over budget.
    """

    def __init__(
        self,
        message: str,
        original_tokens: Optional[int] = None,
        final_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, stage="token_budget_enforcer", context=context)
        self.original_tokens = original_tokens
        self.final_tokens = final_tokens


class SlimZeroResponseWarning(SlimZeroError):
    """
    Response failed intent validation.
    Response is still returned - never suppressed.
    """

    def __init__(
        self,
        message: str,
        similarity: Optional[float] = None,
        threshold: float = 0.60,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, stage="response_validator", context=context)
        self.similarity = similarity
        self.threshold = threshold


class SlimZeroHallucinationFlag(SlimZeroError):
    """
    Hallucination heuristic triggered on response.
    This is a flag, not a guarantee of hallucination.
    """

    def __init__(
        self,
        message: str,
        patterns_matched: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, stage="hallucination_flag", context=context)
        self.patterns_matched = patterns_matched or []


class SlimZeroAgentError(SlimZeroError):
    """Base class for agent-related errors."""

    def __init__(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, stage="agent_loop", context=context)


class SlimZeroCircuitBreaker(SlimZeroAgentError):
    """
    Agent loop halted by budget exhaustion.
    State is checkpointed before raising.
    """

    def __init__(
        self,
        message: str,
        reason: Optional[str] = None,
        steps_taken: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context=context)
        self.reason = reason
        self.steps_taken = steps_taken


class SlimZeroDriftHalt(SlimZeroAgentError):
    """
    Agent loop halted by semantic drift.
    Drift detected when plan diverges from original goal.
    """

    def __init__(
        self,
        message: str,
        drift_similarity: Optional[float] = None,
        threshold: float = 0.75,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context=context)
        self.drift_similarity = drift_similarity
        self.threshold = threshold


class SlimZeroToolValidationError(SlimZeroAgentError):
    """
    Tool call rejected by validator.
    Invalid arguments or unknown tool name.
    """

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        validation_errors: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context=context)
        self.tool_name = tool_name
        self.validation_errors = validation_errors or []


class SlimZeroHumanEscalation(SlimZeroAgentError):
    """
    Agent loop requires human review to resume.
    State is checkpointed before raising.
    """

    def __init__(
        self,
        message: str,
        checkpoint_path: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context=context)
        self.checkpoint_path = checkpoint_path
        self.reason = reason
