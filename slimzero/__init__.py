"""
SlimZero - Zero-overhead prompt compression, response minimisation,
hallucination guarding, and autonomous agent orchestration.

SlimZero is a model-agnostic Python middleware library that sits between
any application and any LLM API.
"""

__version__ = "0.1.0"
__author__ = "SlimZero Contributors"
__license__ = "MIT"

from slimzero.core import SlimZero
from slimzero.schemas import (
    IntentSchema,
    StageInput,
    StageOutput,
    SlimZeroResult,
)
from slimzero.exceptions import (
    SlimZeroError,
    SlimZeroInputError,
    SlimZeroRewriteError,
    SlimZeroSemanticRejection,
    SlimZeroBudgetWarning,
    SlimZeroResponseWarning,
    SlimZeroHallucinationFlag,
    SlimZeroAgentError,
    SlimZeroCircuitBreaker,
    SlimZeroDriftHalt,
    SlimZeroToolValidationError,
    SlimZeroHumanEscalation,
)

__all__ = [
    "SlimZero",
    "IntentSchema",
    "StageInput",
    "StageOutput",
    "SlimZeroResult",
    "SlimZeroError",
    "SlimZeroInputError",
    "SlimZeroRewriteError",
    "SlimZeroSemanticRejection",
    "SlimZeroBudgetWarning",
    "SlimZeroResponseWarning",
    "SlimZeroHallucinationFlag",
    "SlimZeroAgentError",
    "SlimZeroCircuitBreaker",
    "SlimZeroDriftHalt",
    "SlimZeroToolValidationError",
    "SlimZeroHumanEscalation",
]
