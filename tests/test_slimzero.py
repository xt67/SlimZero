"""
Tests for SlimZero Package Structure (US-001)

Verifies that the package structure and exception hierarchy are properly set up.
"""

import pytest
from slimzero import (
    SlimZero,
    IntentSchema,
    StageInput,
    StageOutput,
    SlimZeroResult,
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


class TestExceptionHierarchy:
    """Test that all exceptions exist and have proper hierarchy."""

    def test_slimzero_error_is_base(self):
        """SlimZeroError should be the base exception."""
        assert issubclass(SlimZeroError, Exception)

    def test_input_error_exists(self):
        """SlimZeroInputError should exist and inherit from base."""
        error = SlimZeroInputError("Test error", field_name="prompt")
        assert isinstance(error, SlimZeroError)
        assert error.field_name == "prompt"

    def test_rewrite_error_exists(self):
        """SlimZeroRewriteError should exist."""
        error = SlimZeroRewriteError("Rewrite failed")
        assert isinstance(error, SlimZeroError)
        assert error.stage == "prompt_rewriter"

    def test_semantic_rejection_exists(self):
        """SlimZeroSemanticRejection should exist."""
        error = SlimZeroSemanticRejection(
            "Rejected", similarity=0.85, threshold=0.92
        )
        assert isinstance(error, SlimZeroError)
        assert error.similarity == 0.85

    def test_budget_warning_exists(self):
        """SlimZeroBudgetWarning should exist."""
        error = SlimZeroBudgetWarning(
            "Over budget", original_tokens=1000, final_tokens=1100
        )
        assert isinstance(error, SlimZeroError)
        assert error.original_tokens == 1000

    def test_response_warning_exists(self):
        """SlimZeroResponseWarning should exist."""
        error = SlimZeroResponseWarning(
            "Validation failed", similarity=0.5, threshold=0.6
        )
        assert isinstance(error, SlimZeroError)
        assert error.threshold == 0.6

    def test_hallucination_flag_exists(self):
        """SlimZeroHallucinationFlag should exist."""
        error = SlimZeroHallucinationFlag(
            "Flag raised", patterns_matched=["date_pattern", "citation_pattern"]
        )
        assert isinstance(error, SlimZeroError)
        assert len(error.patterns_matched) == 2

    def test_agent_error_base_exists(self):
        """SlimZeroAgentError should exist as base for agent errors."""
        error = SlimZeroAgentError("Agent error")
        assert isinstance(error, SlimZeroError)
        assert error.stage == "agent_loop"

    def test_circuit_breaker_exists(self):
        """SlimZeroCircuitBreaker should exist."""
        error = SlimZeroCircuitBreaker(
            "Circuit broken", reason="max_steps", steps_taken=20
        )
        assert isinstance(error, SlimZeroAgentError)
        assert error.steps_taken == 20

    def test_drift_halt_exists(self):
        """SlimZeroDriftHalt should exist."""
        error = SlimZeroDriftHalt(
            "Drift detected", drift_similarity=0.6, threshold=0.75
        )
        assert isinstance(error, SlimZeroAgentError)
        assert error.drift_similarity == 0.6

    def test_tool_validation_error_exists(self):
        """SlimZeroToolValidationError should exist."""
        error = SlimZeroToolValidationError(
            "Invalid tool call",
            tool_name="search",
            validation_errors=["missing_argument"],
        )
        assert isinstance(error, SlimZeroAgentError)
        assert error.tool_name == "search"

    def test_human_escalation_exists(self):
        """SlimZeroHumanEscalation should exist."""
        error = SlimZeroHumanEscalation(
            "Needs review",
            checkpoint_path="/path/to/checkpoint.json",
            reason="max_retries",
        )
        assert isinstance(error, SlimZeroAgentError)
        assert error.checkpoint_path == "/path/to/checkpoint.json"


class TestSchemas:
    """Test that all schemas exist and work correctly."""

    def test_intent_schema_exists(self):
        """IntentSchema should exist and be creatable."""
        intent = IntentSchema(
            core_task="Explain machine learning",
            entities=("machine learning",),
            raw_prompt="Can you explain machine learning?",
        )
        assert intent.core_task == "Explain machine learning"
        assert "machine learning" in intent.entities

    def test_intent_schema_hashable(self):
        """IntentSchema should be hashable (frozen)."""
        intent1 = IntentSchema(core_task="Task 1")
        intent2 = IntentSchema(core_task="Task 2")
        intent_set = {intent1, intent2}
        assert len(intent_set) == 2

    def test_intent_schema_serializable(self):
        """IntentSchema should convert to dict."""
        intent = IntentSchema(core_task="Task", entities=("e1",))
        d = intent.to_dict()
        assert d["core_task"] == "Task"
        assert d["entities"] == ["e1"]

    def test_stage_input_exists(self):
        """StageInput should exist."""
        intent = IntentSchema(core_task="Task")
        inp = StageInput(
            prompt="Test prompt",
            intent=intent,
            token_count=100,
        )
        assert inp.prompt == "Test prompt"
        assert inp.token_count == 100

    def test_stage_output_exists(self):
        """StageOutput should exist."""
        out = StageOutput(prompt="Compressed", modified=True, notes="Test")
        assert out.modified is True
        assert out.notes == "Test"

    def test_slimzero_result_exists(self):
        """SlimZeroResult should exist."""
        result = SlimZeroResult(
            response="Answer",
            original_prompt="Question",
            sent_prompt="Q",
            original_input_tokens=100,
            sent_input_tokens=50,
            estimated_output_tokens=200,
            stages_applied=["rewriter", "semantic_guard"],
        )
        assert result.response == "Answer"
        assert result.input_token_savings == 50
        assert result.input_token_savings_percent == 50.0


class TestSlimZeroClass:
    """Test that SlimZero class can be instantiated."""

    def test_slimzero_instantiation(self):
        """SlimZero should be instantiable with default params."""
        sz = SlimZero()
        assert sz.model == "claude-sonnet-4-6"
        assert sz.sim_threshold == 0.92

    def test_slimzero_with_custom_params(self):
        """SlimZero should accept custom parameters."""
        sz = SlimZero(
            model="gpt-4o",
            sim_threshold=0.95,
            few_shot_k=5,
            history_window=6,
            agent_mode=True,
        )
        assert sz.model == "gpt-4o"
        assert sz.sim_threshold == 0.95
        assert sz.few_shot_k == 5
        assert sz.agent_mode is True

    def test_slimzero_has_call_method(self):
        """SlimZero should have a call method."""
        sz = SlimZero()
        assert hasattr(sz, "call")
        assert callable(sz.call)

    def test_slimzero_has_run_goal_method(self):
        """SlimZero should have a run_goal method."""
        sz = SlimZero()
        assert hasattr(sz, "run_goal")
        assert callable(sz.run_goal)
