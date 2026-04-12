"""
SlimZero Data Schemas

Contains all dataclasses used throughout the SlimZero pipeline.
All schemas are serializable and hashable for caching purposes.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List
from enum import Enum


class OutputFormat(Enum):
    """Detected output format for the response."""

    GENERAL = "general"
    CODE = "code"
    LIST = "list"
    TABLE = "table"
    EXPLAIN = "explain"
    UNKNOWN = "unknown"


class HallucinationRiskTier(Enum):
    """Risk tier for hallucination-prone queries."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StageStatus(Enum):
    """Status of a pipeline stage execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class IntentSchema:
    """
    Structured representation of a parsed user prompt.
    Used by downstream stages and response validator.
    Frozen for hashability.
    """

    core_task: str
    entities: tuple = field(default_factory=tuple)
    output_format: OutputFormat = OutputFormat.UNKNOWN
    constraints: tuple = field(default_factory=tuple)
    raw_prompt: str = ""

    def __post_init__(self):
        if not self.core_task and self.raw_prompt:
            object.__setattr__(self, "core_task", self.raw_prompt)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "core_task": self.core_task,
            "entities": list(self.entities),
            "output_format": self.output_format.value,
            "constraints": list(self.constraints),
            "raw_prompt": self.raw_prompt,
        }


@dataclass
class StageInput:
    """
    Input passed to each pipeline stage.
    """

    prompt: str
    intent: IntentSchema
    token_count: int
    system_prompt: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    few_shot_examples: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "prompt": self.prompt[:100] + "..." if len(self.prompt) > 100 else self.prompt,
            "intent": self.intent.to_dict(),
            "token_count": self.token_count,
            "has_system_prompt": self.system_prompt is not None,
            "history_length": len(self.history) if self.history else 0,
            "few_shot_count": len(self.few_shot_examples) if self.few_shot_examples else 0,
            "metadata_keys": list(self.metadata.keys()),
        }


@dataclass
class StageOutput:
    """
    Output from each pipeline stage.
    """

    prompt: str
    modified: bool = False
    notes: str = ""
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "prompt": self.prompt[:100] + "..." if len(self.prompt) > 100 else self.prompt,
            "modified": self.modified,
            "notes": self.notes,
            "token_count": self.token_count,
            "metadata_keys": list(self.metadata.keys()),
        }


@dataclass
class SlimZeroResult:
    """
    Final result returned after pipeline execution.
    """

    response: str
    original_prompt: str
    sent_prompt: str
    original_input_tokens: int
    sent_input_tokens: int
    estimated_output_tokens: int
    stages_applied: List[str]
    semantic_similarity: Optional[float] = None
    hallucination_risk_tier: HallucinationRiskTier = HallucinationRiskTier.LOW
    response_validated: bool = True
    flags_raised: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def input_token_savings(self) -> int:
        """Calculate input token savings."""
        return self.original_input_tokens - self.sent_input_tokens

    @property
    def input_token_savings_percent(self) -> float:
        """Calculate input token savings as percentage."""
        if self.original_input_tokens == 0:
            return 0.0
        return (self.input_token_savings / self.original_input_tokens) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "response": self.response,
            "original_prompt": self.original_prompt,
            "sent_prompt": self.sent_prompt,
            "original_input_tokens": self.original_input_tokens,
            "sent_input_tokens": self.sent_input_tokens,
            "input_token_savings": self.input_token_savings,
            "input_token_savings_percent": self.input_token_savings_percent,
            "estimated_output_tokens": self.estimated_output_tokens,
            "stages_applied": self.stages_applied,
            "semantic_similarity": self.semantic_similarity,
            "hallucination_risk_tier": self.hallucination_risk_tier.value,
            "response_validated": self.response_validated,
            "flags_raised": self.flags_raised,
            "metadata": self.metadata,
        }


@dataclass
class SavingsStats:
    """
    Cumulative savings statistics for a session.
    """

    total_calls: int = 0
    total_input_tokens_original: int = 0
    total_input_tokens_sent: int = 0
    total_output_tokens: int = 0
    total_savings: int = 0

    model_pricing: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "claude-sonnet-4-6": {"input": 0.000003, "output": 0.000015},
        "claude-opus-4-6": {"input": 0.000015, "output": 0.000075},
        "gpt-4o": {"input": 0.000005, "output": 0.000015},
        "default": {"input": 0.000005, "output": 0.000015},
    })

    @property
    def estimated_cost_savings(self) -> float:
        """Calculate estimated cost savings in USD."""
        return self.total_savings * 0.000005

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "total_calls": self.total_calls,
            "total_input_tokens_original": self.total_input_tokens_original,
            "total_input_tokens_sent": self.total_input_tokens_sent,
            "total_output_tokens": self.total_output_tokens,
            "total_savings": self.total_savings,
            "estimated_cost_savings_usd": self.estimated_cost_savings,
        }
