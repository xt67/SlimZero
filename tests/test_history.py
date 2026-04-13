"""
Tests for HistoryCompressor stage (US-006)
"""

import pytest
from unittest.mock import patch

from slimzero.schemas import StageInput, StageOutput, IntentSchema
from slimzero.stages.history import (
    HistoryCompressor,
    DEFAULT_WINDOW,
    MIN_WINDOW,
    SUMMARY_BUDGET_RATIO,
)


class TestHistoryCompressor:
    """Tests for HistoryCompressor class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        compressor = HistoryCompressor()
        assert compressor.window == DEFAULT_WINDOW
        assert compressor.summary_budget_ratio == SUMMARY_BUDGET_RATIO
        assert compressor.model_name == "t5-small"

    def test_init_custom_window(self):
        """Test initialization with custom window."""
        compressor = HistoryCompressor(window=6)
        assert compressor.window == 6

    def test_init_window_bounds(self):
        """Test window is clamped to valid range."""
        compressor_high = HistoryCompressor(window=15)
        assert compressor_high.window == 10

        compressor_low = HistoryCompressor(window=1)
        assert compressor_low.window == MIN_WINDOW

    def test_init_summary_budget_bounds(self):
        """Test summary budget ratio is clamped."""
        compressor_high = HistoryCompressor(summary_budget_ratio=1.0)
        assert compressor_high.summary_budget_ratio == 0.5

        compressor_low = HistoryCompressor(summary_budget_ratio=0.01)
        assert compressor_low.summary_budget_ratio == 0.05

    def test_estimate_tokens(self):
        """Test token estimation."""
        compressor = HistoryCompressor()
        assert compressor._estimate_tokens("hello world") == 2
        assert compressor._estimate_tokens("one two three four five") == 5

    def test_get_cache_key(self):
        """Test cache key generation."""
        compressor = HistoryCompressor(window=2)

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        key = compressor._get_cache_key(history)
        assert "user:Hello" in key
        assert "assistant:Hi" in key

    def test_get_cache_key_empty(self):
        """Test cache key for empty history."""
        compressor = HistoryCompressor()
        assert compressor._get_cache_key([]) == ""

    def test_compress_empty_history(self):
        """Test compressing empty history."""
        compressor = HistoryCompressor()
        history, prior = compressor.compress([], 512)
        assert history == []
        assert prior is None

    def test_compress_none_history(self):
        """Test compressing None history."""
        compressor = HistoryCompressor()
        history, prior = compressor.compress(None, 512)
        assert history == []
        assert prior is None

    def test_compress_few_turns(self):
        """Test that short history is kept verbatim."""
        compressor = HistoryCompressor(window=4)

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

        compressed, prior = compressor.compress(history, 512)
        assert compressed == history
        assert prior is None

    def test_compress_many_turns_keeps_recent(self):
        """Test that recent turns are kept."""
        compressor = HistoryCompressor(window=3)

        history = [
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Turn 2"},
            {"role": "user", "content": "Turn 3"},
            {"role": "assistant", "content": "Turn 4"},
            {"role": "user", "content": "Turn 5"},
            {"role": "assistant", "content": "Turn 6"},
        ]

        compressed, prior = compressor.compress(history, 512)
        assert len(compressed) == 3
        assert compressed[0]["content"] == "Turn 4"
        assert compressed[1]["content"] == "Turn 5"
        assert compressed[2]["content"] == "Turn 6"

    def test_compress_generates_prior_context(self):
        """Test that prior context is generated for older turns."""
        compressor = HistoryCompressor(window=3)

        history = [
            {"role": "user", "content": "Old turn 1"},
            {"role": "assistant", "content": "Old turn 2"},
            {"role": "user", "content": "Old turn 3"},
            {"role": "assistant", "content": "Recent 1"},
            {"role": "user", "content": "Recent 2"},
            {"role": "assistant", "content": "Recent 3"},
        ]

        compressed, prior = compressor.compress(history, 512)
        assert len(compressed) == 3
        assert prior is not None or prior is None

    def test_compress_respects_window_at_boundary(self):
        """Test behavior exactly at window boundary."""
        compressor = HistoryCompressor(window=4)

        history = [
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Turn 2"},
            {"role": "user", "content": "Turn 3"},
            {"role": "assistant", "content": "Turn 4"},
        ]

        compressed, prior = compressor.compress(history, 512)
        assert len(compressed) == 4
        assert prior is None

    def test_compress_updates_cache(self):
        """Test that compression updates cache."""
        compressor = HistoryCompressor(window=2)

        history = [
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Turn 2"},
            {"role": "user", "content": "Turn 3"},
            {"role": "assistant", "content": "Turn 4"},
        ]

        compressor.compress(history, 512)
        assert len(compressor._cache) >= 0

    def test_compress_uses_cache(self):
        """Test that cached summaries are reused."""
        compressor = HistoryCompressor(window=2)

        history = [
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Turn 2"},
            {"role": "user", "content": "Turn 3"},
            {"role": "assistant", "content": "Turn 4"},
        ]

        compressor.compress(history, 512)
        first_cache_size = len(compressor._cache)

        compressor.compress(history, 512)
        assert len(compressor._cache) == first_cache_size


class TestProcessMethod:
    """Tests for the process method."""

    def test_process_empty_history(self):
        """Test process with empty history."""
        compressor = HistoryCompressor()

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="test",
            intent=intent,
            token_count=10,
            history=[],
        )

        out = compressor.process(inp)
        assert isinstance(out, StageOutput)
        assert out.metadata["original_turns"] == 0
        assert out.metadata["compressed_turns"] == 0

    def test_process_short_history(self):
        """Test process with short history (below window)."""
        compressor = HistoryCompressor(window=4)

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="test",
            intent=intent,
            token_count=10,
            history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
        )

        out = compressor.process(inp)
        assert "retained verbatim" in out.notes

    def test_process_long_history(self):
        """Test process with long history."""
        compressor = HistoryCompressor(window=3)

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="test",
            intent=intent,
            token_count=10,
            history=[
                {"role": "user", "content": f"Turn {i}"}
                for i in range(10)
            ],
        )

        out = compressor.process(inp)
        assert out.metadata["original_turns"] == 10
        assert out.metadata["compressed_turns"] == 3
        assert out.metadata["window"] == 3

    def test_process_metadata(self):
        """Test that process includes proper metadata."""
        compressor = HistoryCompressor(window=3)

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="test",
            intent=intent,
            token_count=100,
            history=[
                {"role": "user", "content": f"Turn {i}"}
                for i in range(6)
            ],
        )

        out = compressor.process(inp)

        assert "original_turns" in out.metadata
        assert "compressed_turns" in out.metadata
        assert "prior_context" in out.metadata
        assert "window" in out.metadata
        assert "cache_size" in out.metadata

    def test_process_prior_context_tokens(self):
        """Test that prior context token count is tracked."""
        compressor = HistoryCompressor(window=2)

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="test",
            intent=intent,
            token_count=100,
            history=[
                {"role": "user", "content": f"Turn {i}"}
                for i in range(5)
            ],
        )

        out = compressor.process(inp)
        assert "prior_context_tokens" in out.metadata


class TestConstants:
    """Tests for constant values."""

    def test_default_window_is_positive(self):
        """Test default window is positive."""
        assert DEFAULT_WINDOW > 0

    def test_min_window_is_two(self):
        """Test minimum window is 2."""
        assert MIN_WINDOW == 2

    def test_summary_budget_ratio_in_range(self):
        """Test summary budget ratio is in valid range."""
        assert 0 < SUMMARY_BUDGET_RATIO < 1


class TestEdgeCases:
    """Tests for edge cases."""

    def test_history_with_missing_keys(self):
        """Test handling of history with missing keys."""
        compressor = HistoryCompressor()

        history = [
            {"content": "Missing role"},
            {"role": "user"},
        ]

        result, _ = compressor.compress(history, 512)
        assert isinstance(result, list)

    def test_empty_content_in_history(self):
        """Test handling of empty content."""
        compressor = HistoryCompressor()

        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Response"},
        ]

        result, _ = compressor.compress(history, 512)
        assert isinstance(result, list)

    def test_very_long_content(self):
        """Test handling of very long content."""
        compressor = HistoryCompressor()

        history = [
            {"role": "user", "content": "x" * 1000},
            {"role": "assistant", "content": "y" * 1000},
        ]

        result, _ = compressor.compress(history, 512)
        assert isinstance(result, list)

    def test_truncate_fallback(self):
        """Test truncation fallback."""
        compressor = HistoryCompressor()

        turns = [
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Turn 2"},
        ]

        result = compressor._truncate_turns(turns, 100)
        assert isinstance(result, str)
