"""
Tests for SlimZero core package
"""

import pytest
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
from slimzero.schemas import (
    IntentSchema,
    StageInput,
    StageOutput,
    SlimZeroResult,
    OutputFormat,
    HallucinationRiskTier,
    StageStatus,
)
from slimzero import SlimZero


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_slimzero_error_is_base(self):
        """Test SlimZeroError is the base class."""
        assert issubclass(SlimZeroInputError, SlimZeroError)
        assert issubclass(SlimZeroRewriteError, SlimZeroError)
        assert issubclass(SlimZeroSemanticRejection, SlimZeroError)

    def test_input_error_exists(self):
        """Test SlimZeroInputError exists."""
        with pytest.raises(SlimZeroInputError):
            raise SlimZeroInputError("test")

    def test_rewrite_error_exists(self):
        """Test SlimZeroRewriteError exists."""
        with pytest.raises(SlimZeroRewriteError):
            raise SlimZeroRewriteError("test")

    def test_semantic_rejection_exists(self):
        """Test SlimZeroSemanticRejection exists."""
        with pytest.raises(SlimZeroSemanticRejection):
            raise SlimZeroSemanticRejection("test", similarity=0.5, threshold=0.9)

    def test_budget_warning_exists(self):
        """Test SlimZeroBudgetWarning exists."""
        with pytest.raises(SlimZeroBudgetWarning):
            raise SlimZeroBudgetWarning("test")

    def test_response_warning_exists(self):
        """Test SlimZeroResponseWarning exists."""
        with pytest.raises(SlimZeroResponseWarning):
            raise SlimZeroResponseWarning("test")

    def test_hallucination_flag_exists(self):
        """Test SlimZeroHallucinationFlag exists."""
        with pytest.raises(SlimZeroHallucinationFlag):
            raise SlimZeroHallucinationFlag("test")

    def test_agent_error_base_exists(self):
        """Test SlimZeroAgentError exists."""
        assert issubclass(SlimZeroAgentError, SlimZeroError)

    def test_circuit_breaker_exists(self):
        """Test SlimZeroCircuitBreaker exists."""
        with pytest.raises(SlimZeroCircuitBreaker):
            raise SlimZeroCircuitBreaker("test", reason="max_steps", steps_taken=20)

    def test_drift_halt_exists(self):
        """Test SlimZeroDriftHalt exists."""
        with pytest.raises(SlimZeroDriftHalt):
            raise SlimZeroDriftHalt("test", drift_similarity=0.5, threshold=0.75)

    def test_tool_validation_error_exists(self):
        """Test SlimZeroToolValidationError exists."""
        with pytest.raises(SlimZeroToolValidationError):
            raise SlimZeroToolValidationError("test", tool_name="test_tool")

    def test_human_escalation_exists(self):
        """Test SlimZeroHumanEscalation exists."""
        with pytest.raises(SlimZeroHumanEscalation):
            raise SlimZeroHumanEscalation("test")


class TestSchemas:
    """Tests for data schemas."""

    def test_intent_schema_exists(self):
        """Test IntentSchema exists."""
        schema = IntentSchema(core_task="test")
        assert schema.core_task == "test"

    def test_intent_schema_hashable(self):
        """Test IntentSchema is hashable."""
        schema1 = IntentSchema(core_task="test", entities=("a", "b"))
        schema2 = IntentSchema(core_task="test", entities=("a", "b"))
        assert hash(schema1) == hash(schema2)

    def test_intent_schema_serializable(self):
        """Test IntentSchema is serializable."""
        schema = IntentSchema(core_task="test", entities=("a",))
        data = schema.to_dict()
        assert isinstance(data, dict)
        assert data["core_task"] == "test"

    def test_stage_input_exists(self):
        """Test StageInput exists."""
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=4)
        assert inp.prompt == "test"

    def test_stage_output_exists(self):
        """Test StageOutput exists."""
        out = StageOutput(prompt="test", modified=True)
        assert out.prompt == "test"
        assert out.modified is True

    def test_slimzero_result_exists(self):
        """Test SlimZeroResult exists."""
        result = SlimZeroResult(
            response="test",
            original_prompt="test",
            sent_prompt="test",
            original_input_tokens=4,
            sent_input_tokens=3,
            estimated_output_tokens=10,
            stages_applied=["test"],
        )
        assert result.response == "test"


class TestSlimZeroClass:
    """Tests for SlimZero class."""

    def test_slimzero_instantiation(self):
        """Test SlimZero can be instantiated."""
        sz = SlimZero()
        assert sz is not None

    def test_slimzero_with_custom_params(self):
        """Test SlimZero with custom parameters."""
        sz = SlimZero(
            model="gpt-4o",
            token_budget=1024,
            sim_threshold=0.95,
        )
        assert sz is not None
        assert sz.token_budget == 1024
        assert sz.sim_threshold == 0.95

    def test_slimzero_has_call_method(self):
        """Test SlimZero has call method."""
        sz = SlimZero()
        assert hasattr(sz, "call")

    def test_slimzero_has_run_goal_method(self):
        """Test SlimZero has run_goal method."""
        sz = SlimZero()
        assert hasattr(sz, "run_goal")

    def test_slimzero_has_get_stats_method(self):
        """Test SlimZero has get_stats method."""
        sz = SlimZero()
        assert hasattr(sz, "get_stats")

    def test_slimzero_has_export_methods(self):
        """Test SlimZero has export methods."""
        sz = SlimZero()
        assert hasattr(sz, "export_stats_json")
        assert hasattr(sz, "export_stats_markdown")

    def test_slimzero_call_empty_prompt_raises(self):
        """Test SlimZero call with empty prompt raises."""
        sz = SlimZero()
        with pytest.raises(SlimZeroInputError):
            sz.call("")

    def test_slimzero_call_none_prompt_raises(self):
        """Test SlimZero call with None prompt raises."""
        sz = SlimZero()
        with pytest.raises(SlimZeroInputError):
            sz.call(None)

    def test_slimzero_call_with_system_prompt(self):
        """Test SlimZero call with system prompt."""
        sz = SlimZero(model="mock")
        result = sz.call("test prompt", system_prompt="You are helpful.")
        assert isinstance(result, SlimZeroResult)
        assert result.original_prompt == "test prompt"

    def test_slimzero_call_returns_result(self):
        """Test SlimZero call returns SlimZeroResult."""
        sz = SlimZero(model="mock")
        result = sz.call("Explain Python")
        assert isinstance(result, SlimZeroResult)
        assert result.response is not None
        assert result.stages_applied is not None

    def test_slimzero_get_stats(self):
        """Test get_stats returns dict."""
        sz = SlimZero()
        stats = sz.get_stats()
        assert isinstance(stats, dict)
        assert "cumulative_tokens_saved" in stats
        assert "total_calls" in stats

    def test_slimzero_export_json(self):
        """Test export_stats_json returns string."""
        sz = SlimZero()
        json_str = sz.export_stats_json()
        assert isinstance(json_str, str)
        assert "cumulative_tokens_saved" in json_str

    def test_slimzero_export_markdown(self):
        """Test export_stats_markdown returns string."""
        sz = SlimZero()
        md_str = sz.export_stats_markdown()
        assert isinstance(md_str, str)
        assert "SlimZero Session Summary" in md_str
