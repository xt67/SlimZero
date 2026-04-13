"""
Tests for SavingsLogger (US-012)
"""

import pytest
import json
from pathlib import Path

from slimzero.schemas import HallucinationRiskTier
from slimzero.post.logger import SavingsLogger, DEFAULT_COST_PER_1K_TOKENS


class TestSavingsLogger:
    """Tests for SavingsLogger class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        logger = SavingsLogger()
        assert logger.cost_per_1k_tokens == DEFAULT_COST_PER_1K_TOKENS

    def test_init_custom_cost(self):
        """Test initialization with custom cost."""
        logger = SavingsLogger(cost_per_1k_tokens=0.005)
        assert logger.cost_per_1k_tokens == 0.005

    def test_current_timestamp_format(self):
        """Test timestamp format."""
        logger = SavingsLogger()
        ts = logger._current_timestamp()
        assert "T" in ts
        assert ts.endswith("Z")

    def test_log_call_basic(self):
        """Test basic call logging."""
        logger = SavingsLogger()

        result = logger.log_call(
            original_input_tokens=100,
            sent_input_tokens=80,
        )

        assert result["original_input_tokens"] == 100
        assert result["sent_input_tokens"] == 80
        assert result["delta_input"] == 20
        assert "timestamp" in result

    def test_log_call_with_stages(self):
        """Test call logging with stages."""
        logger = SavingsLogger()

        result = logger.log_call(
            original_input_tokens=100,
            sent_input_tokens=70,
            stages_applied=["intent", "rewriter", "guard"],
        )

        assert len(result["stages_applied"]) == 3
        assert "intent" in result["stages_applied"]

    def test_log_call_with_similarity(self):
        """Test call logging with similarity."""
        logger = SavingsLogger()

        result = logger.log_call(
            original_input_tokens=100,
            sent_input_tokens=80,
            semantic_similarity=0.95,
        )

        assert result["semantic_similarity"] == 0.95

    def test_log_call_with_risk_tier(self):
        """Test call logging with risk tier."""
        logger = SavingsLogger()

        result = logger.log_call(
            original_input_tokens=100,
            sent_input_tokens=80,
            hallucination_risk_tier=HallucinationRiskTier.HIGH,
        )

        assert result["hallucination_risk_tier"] == "high"

    def test_log_call_with_context(self):
        """Test call logging with context."""
        logger = SavingsLogger()

        result = logger.log_call(
            original_input_tokens=100,
            sent_input_tokens=80,
            context={"user_id": "123", "session": "abc"},
        )

        assert result["context"]["user_id"] == "123"

    def test_cumulative_tokens_accumulates(self):
        """Test that cumulative tokens accumulate."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)
        logger.log_call(original_input_tokens=100, sent_input_tokens=70)

        stats = logger.get_cumulative_stats()
        assert stats["cumulative_tokens_saved"] == 50

    def test_cumulative_cost_accumulates(self):
        """Test that cumulative cost accumulates."""
        logger = SavingsLogger(cost_per_1k_tokens=0.001)

        logger.log_call(original_input_tokens=1000, sent_input_tokens=800)
        logger.log_call(original_input_tokens=1000, sent_input_tokens=900)

        stats = logger.get_cumulative_stats()
        assert stats["cumulative_estimated_cost_usd"] > 0

    def test_total_calls_counted(self):
        """Test that total calls are counted."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)
        logger.log_call(original_input_tokens=100, sent_input_tokens=70)

        stats = logger.get_cumulative_stats()
        assert stats["total_calls"] == 2

    def test_avg_tokens_per_call(self):
        """Test average tokens per call calculation."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)
        logger.log_call(original_input_tokens=100, sent_input_tokens=60)

        stats = logger.get_cumulative_stats()
        assert stats["avg_tokens_saved_per_call"] == 30.0


class TestExportMethods:
    """Tests for export methods."""

    def test_export_json_returns_string(self):
        """Test JSON export returns string."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)

        json_str = logger.export_json()
        assert isinstance(json_str, str)
        assert "cumulative_tokens_saved" in json_str

    def test_export_json_valid_json(self):
        """Test JSON export is valid JSON."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)

        json_str = logger.export_json()
        data = json.loads(json_str)
        assert "stats" in data
        assert "calls" in data

    def test_export_json_to_file(self, tmp_path):
        """Test JSON export to file."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)

        filepath = tmp_path / "test_export.json"
        logger.export_json(str(filepath))

        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert data["stats"]["total_calls"] == 1

    def test_export_markdown_returns_string(self):
        """Test Markdown export returns string."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)

        md_str = logger.export_markdown()
        assert isinstance(md_str, str)
        assert "# SlimZero Session Summary" in md_str

    def test_export_markdown_contains_stats(self):
        """Test Markdown contains statistics."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)

        md_str = logger.export_markdown()
        assert "Total Calls" in md_str
        assert "Tokens Saved" in md_str

    def test_export_markdown_to_file(self, tmp_path):
        """Test Markdown export to file."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)

        filepath = tmp_path / "test_export.md"
        logger.export_markdown(str(filepath))

        assert filepath.exists()
        assert "# SlimZero Session Summary" in filepath.read_text()


class TestReset:
    """Tests for reset method."""

    def test_reset_clears_logs(self):
        """Test reset clears session logs."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)
        logger.reset()

        assert len(logger._session_logs) == 0

    def test_reset_clears_cumulative(self):
        """Test reset clears cumulative stats."""
        logger = SavingsLogger()

        logger.log_call(original_input_tokens=100, sent_input_tokens=80)
        logger.reset()

        stats = logger.get_cumulative_stats()
        assert stats["cumulative_tokens_saved"] == 0
        assert stats["total_calls"] == 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_log_call_zero_delta(self):
        """Test logging with zero delta."""
        logger = SavingsLogger()

        result = logger.log_call(
            original_input_tokens=100,
            sent_input_tokens=100,
        )

        assert result["delta_input"] == 0

    def test_log_call_negative_delta(self):
        """Test logging with negative delta (no savings)."""
        logger = SavingsLogger()

        result = logger.log_call(
            original_input_tokens=100,
            sent_input_tokens=120,
        )

        assert result["delta_input"] == -20

    def test_get_stats_empty_session(self):
        """Test getting stats from empty session."""
        logger = SavingsLogger()

        stats = logger.get_cumulative_stats()
        assert stats["total_calls"] == 0
        assert stats["cumulative_tokens_saved"] == 0

    def test_export_empty_session(self):
        """Test exporting empty session."""
        logger = SavingsLogger()

        json_str = logger.export_json()
        md_str = logger.export_markdown()

        assert "total_calls" in json_str
        assert "# SlimZero Session Summary" in md_str
