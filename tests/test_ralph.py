"""
Tests for RalphLoop (US-015)
"""

import pytest

from slimzero.agent.ralph import RalphLoop, ToolValidator, ActionAuditor, ActionType
from slimzero.exceptions import (
    SlimZeroCircuitBreaker,
    SlimZeroDriftHalt,
    SlimZeroToolValidationError,
)


class TestToolValidator:
    """Tests for ToolValidator."""

    def test_register_tool(self):
        """Test tool registration."""
        validator = ToolValidator()
        validator.register_tool("test_tool", {"required": ["arg1"], "properties": {}})
        assert "test_tool" in validator._known_tools

    def test_validate_valid_call(self):
        """Test validating valid tool call."""
        validator = ToolValidator()
        validator.register_tool("echo", {
            "required": ["message"],
            "properties": {"message": {"type": "string"}},
        })
        is_valid, error = validator.validate("echo", {"message": "hello"})
        assert is_valid is True
        assert error is None

    def test_validate_missing_argument(self):
        """Test validation with missing argument."""
        validator = ToolValidator()
        validator.register_tool("echo", {
            "required": ["message"],
            "properties": {"message": {"type": "string"}},
        })
        is_valid, error = validator.validate("echo", {})
        assert is_valid is False
        assert "message" in error

    def test_validate_unknown_tool(self):
        """Test validation of unknown tool."""
        validator = ToolValidator()
        is_valid, error = validator.validate("unknown", {})
        assert is_valid is False
        assert "Unknown tool" in error


class TestActionAuditor:
    """Tests for ActionAuditor."""

    def test_log_action(self):
        """Test logging an action."""
        auditor = ActionAuditor()
        auditor.log(ActionType.THINK, step=1)
        assert len(auditor.get_log()) == 1

    def test_log_with_tool_call(self):
        """Test logging tool call."""
        auditor = ActionAuditor()
        auditor.log(
            ActionType.TOOL_CALL,
            tool_name="echo",
            arguments={"message": "hello"},
            tokens_used=50,
            step=1,
        )
        log = auditor.get_log()[0]
        assert log["tool_name"] == "echo"
        assert log["tokens_used"] == 50

    def test_export_log(self):
        """Test exporting log as JSON."""
        auditor = ActionAuditor()
        auditor.log(ActionType.THINK, step=1)
        json_str = auditor.export_log()
        assert "think" in json_str
        assert "step" in json_str


class TestRalphLoop:
    """Tests for RalphLoop."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        loop = RalphLoop()
        assert loop.max_steps == 20
        assert loop.max_retries_per_step == 3
        assert loop.drift_threshold == 0.75

    def test_init_custom(self):
        """Test initialization with custom values."""
        loop = RalphLoop(max_steps=10, drift_threshold=0.8)
        assert loop.max_steps == 10
        assert loop.drift_threshold == 0.8

    def test_register_tool(self):
        """Test registering a tool."""
        loop = RalphLoop()
        loop.register_tool("test", {"required": [], "properties": {}})
        assert "test" in loop._tool_validator._known_tools

    def test_check_circuit_breaker_max_steps(self):
        """Test circuit breaker raises on max steps."""
        loop = RalphLoop(max_steps=5)
        loop._step_count = 5
        with pytest.raises(SlimZeroCircuitBreaker):
            loop._check_circuit_breaker()

    def test_check_circuit_breaker_max_tokens(self):
        """Test circuit breaker raises on max tokens."""
        loop = RalphLoop(max_total_tokens=100)
        loop._total_tokens = 100
        with pytest.raises(SlimZeroCircuitBreaker):
            loop._check_circuit_breaker()

    def test_validate_tool_call_valid(self):
        """Test validating valid tool call."""
        loop = RalphLoop()
        loop.register_tool("echo", {
            "required": ["msg"],
            "properties": {"msg": {}},
        })
        loop._validate_tool_call("echo", {"msg": "hello"})

    def test_validate_tool_call_invalid(self):
        """Test validating invalid tool call."""
        loop = RalphLoop()
        loop.register_tool("echo", {
            "required": ["msg"],
            "properties": {"msg": {}},
        })
        with pytest.raises(SlimZeroToolValidationError):
            loop._validate_tool_call("echo", {})

    def test_run_basic(self):
        """Test basic run."""
        loop = RalphLoop(max_steps=2)
        result = loop.run("Test goal")
        assert "audit_log" in result
        assert result["steps"] == 1

    def test_run_with_tools(self):
        """Test run with tools."""
        loop = RalphLoop(max_steps=2)
        tools = [{"name": "test", "parameters": {"required": [], "properties": {}}}]
        result = loop.run("Test goal", tools=tools)
        assert "audit_log" in result

    def test_circuit_breaker_raises_on_step_limit(self):
        """Circuit breaker raises when manually triggered."""
        from slimzero.exceptions import SlimZeroCircuitBreaker
        loop = RalphLoop(max_steps=5)
        loop._step_count = 5
        with pytest.raises(SlimZeroCircuitBreaker):
            loop._check_circuit_breaker()

    def test_run_returns_max_steps_when_exhausted(self):
        """Run returns max_steps_reached when loop exhausts all steps."""
        loop = RalphLoop(max_steps=1)
        result = loop.run("Test goal")
        assert result["result"] == "max_steps_reached"
        assert result["steps"] == 1

    def test_get_stats(self):
        """Test getting stats."""
        loop = RalphLoop()
        loop.run("Test")
        stats = loop.get_stats()
        assert "steps_taken" in stats
        assert "audit_entries" in stats
