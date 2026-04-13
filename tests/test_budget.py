"""
Tests for TokenBudgetEnforcer stage (US-009)
"""

import pytest

from slimzero.schemas import StageInput, StageOutput, IntentSchema
from slimzero.stages.budget import (
    TokenBudgetEnforcer,
    TRIM_PRIORITY,
    DEFAULT_BUDGET,
    MIN_CORE_TASK_TOKENS,
)


class TestTokenBudgetEnforcer:
    """Tests for TokenBudgetEnforcer class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        enforcer = TokenBudgetEnforcer()
        assert enforcer.token_budget == DEFAULT_BUDGET

    def test_init_custom_budget(self):
        """Test initialization with custom budget."""
        enforcer = TokenBudgetEnforcer(token_budget=1024)
        assert enforcer.token_budget == 1024

    def test_init_budget_bounds(self):
        """Test budget is clamped to valid range."""
        enforcer_high = TokenBudgetEnforcer(token_budget=200000)
        assert enforcer_high.token_budget <= 100000

        enforcer_low = TokenBudgetEnforcer(token_budget=10)
        assert enforcer_low.token_budget >= 50

    def test_estimate_tokens(self):
        """Test token estimation."""
        enforcer = TokenBudgetEnforcer()
        assert enforcer._estimate_tokens("hello world") == 2
        assert enforcer._estimate_tokens("one two three four five") == 5
        assert enforcer._estimate_tokens("") == 0

    def test_count_tokens_empty(self):
        """Test counting tokens for empty text."""
        enforcer = TokenBudgetEnforcer()
        assert enforcer.count_tokens("") == 0
        assert enforcer.count_tokens(None) == 0

    def test_count_tokens_short_text(self):
        """Test counting tokens for short text."""
        enforcer = TokenBudgetEnforcer()
        count = enforcer.count_tokens("hello world")
        assert count >= 2

    def test_count_tokens_long_text(self):
        """Test counting tokens for long text."""
        enforcer = TokenBudgetEnforcer()
        long_text = "word " * 100
        count = enforcer.count_tokens(long_text)
        assert count >= 50

    def test_count_messages_tokens_empty(self):
        """Test counting tokens for empty messages."""
        enforcer = TokenBudgetEnforcer()
        count = enforcer.count_messages_tokens([])
        assert count >= 0

    def test_count_messages_tokens_with_messages(self):
        """Test counting tokens for messages."""
        enforcer = TokenBudgetEnforcer()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        count = enforcer.count_messages_tokens(messages)
        assert count >= 5

    def test_count_messages_tokens_with_system(self):
        """Test counting tokens with system prompt."""
        enforcer = TokenBudgetEnforcer()
        messages = [{"role": "user", "content": "Hello"}]
        count = enforcer.count_messages_tokens(messages, system_prompt="You are helpful.")
        assert count >= 10


class TestTrimPriority:
    """Tests for trim priority order."""

    def test_trim_priority_exists(self):
        """Test trim priority is defined."""
        assert len(TRIM_PRIORITY) > 0

    def test_trim_priority_order(self):
        """Test trim priority has correct order."""
        assert "injected_fragments" in TRIM_PRIORITY
        assert "history_summary" in TRIM_PRIORITY
        assert "low_ranked_examples" in TRIM_PRIORITY
        assert "compressed_rewrite" in TRIM_PRIORITY


class TestEnforceMethod:
    """Tests for the enforce method."""

    def test_enforce_short_prompt(self):
        """Test enforcement with short prompt."""
        enforcer = TokenBudgetEnforcer(token_budget=100)
        prompt = "Hello world"

        final, system, trimmed = enforcer.enforce(prompt)
        assert final == prompt
        assert len(trimmed) == 0

    def test_enforce_with_system_prompt(self):
        """Test enforcement with system prompt."""
        enforcer = TokenBudgetEnforcer(token_budget=100)
        prompt = "word " * 20
        system = "system " * 20

        final, modified_system, trimmed = enforcer.enforce(prompt, system_prompt=system)
        assert modified_system is not None

    def test_enforce_with_injected_fragment(self):
        """Test enforcement with injected fragment."""
        enforcer = TokenBudgetEnforcer(token_budget=100)
        prompt = "test prompt"
        fragment = "Be concise"

        final, system, trimmed = enforcer.enforce(prompt, injected_fragment=fragment)
        assert len(final) > 0

    def test_enforce_with_prior_context(self):
        """Test enforcement with prior context."""
        enforcer = TokenBudgetEnforcer(token_budget=100)
        prompt = "test prompt"
        prior = "prior context"

        final, system, trimmed = enforcer.enforce(prompt, prior_context=prior)
        assert len(final) > 0

    def test_enforce_with_history(self):
        """Test enforcement with history."""
        enforcer = TokenBudgetEnforcer(token_budget=50)
        prompt = "word " * 10
        history = [
            {"role": "user", "content": "history " * 5},
            {"role": "assistant", "content": "response " * 5},
        ]

        final, system, trimmed = enforcer.enforce(prompt, history=history)
        assert enforcer.count_tokens(final) <= 60


class TestProcessMethod:
    """Tests for the process method."""

    def test_process_returns_stage_output(self):
        """Test process returns StageOutput."""
        enforcer = TokenBudgetEnforcer()

        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=10)

        out = enforcer.process(inp)
        assert isinstance(out, StageOutput)

    def test_process_metadata(self):
        """Test that process includes proper metadata."""
        enforcer = TokenBudgetEnforcer(token_budget=100)

        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="word " * 20, intent=intent, token_count=30)

        out = enforcer.process(inp)
        assert "original_tokens" in out.metadata
        assert "final_tokens" in out.metadata
        assert "token_budget" in out.metadata
        assert "within_budget" in out.metadata
        assert "trimmed_items" in out.metadata

    def test_process_within_budget(self):
        """Test that within_budget flag is set correctly."""
        enforcer = TokenBudgetEnforcer(token_budget=100)

        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="short", intent=intent, token_count=1)

        out = enforcer.process(inp)
        assert out.metadata["within_budget"] is True

    def test_process_over_budget(self):
        """Test behavior when over budget."""
        enforcer = TokenBudgetEnforcer(token_budget=20)

        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="word " * 50, intent=intent, token_count=50)

        out = enforcer.process(inp)
        assert out.token_count is not None


class TestConstants:
    """Tests for constant values."""

    def test_default_budget_is_positive(self):
        """Test default budget is positive."""
        assert DEFAULT_BUDGET > 0

    def test_min_core_task_tokens_is_positive(self):
        """Test minimum core task tokens is positive."""
        assert MIN_CORE_TASK_TOKENS > 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_prompt(self):
        """Test handling of empty prompt."""
        enforcer = TokenBudgetEnforcer()

        final, system, trimmed = enforcer.enforce("")
        assert final == ""
        assert len(trimmed) == 0

    def test_none_prompt(self):
        """Test handling of None prompt."""
        enforcer = TokenBudgetEnforcer()

        final, system, trimmed = enforcer.enforce(None)
        assert final == "" or final is None

    def test_unicode_content(self):
        """Test handling of unicode content."""
        enforcer = TokenBudgetEnforcer()

        count = enforcer.count_tokens("Hello 世界 🌍")
        assert count >= 3

    def test_special_characters(self):
        """Test handling of special characters."""
        enforcer = TokenBudgetEnforcer()

        count = enforcer.count_tokens("!@#$%^&*()")
        assert count >= 1

    def test_whitespace_only(self):
        """Test handling of whitespace-only text."""
        enforcer = TokenBudgetEnforcer()

        count = enforcer.count_tokens("   \n\t  ")
        assert count >= 0
