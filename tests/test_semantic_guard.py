"""
Tests for SemanticGuard stage (US-003)
"""

import pytest
from unittest.mock import patch

from slimzero.schemas import StageInput, StageOutput, IntentSchema
from slimzero.stages.semantic_guard import SemanticGuard, MIN_THRESHOLD, DEFAULT_THRESHOLD
from slimzero.exceptions import SlimZeroSemanticRejection


class TestSemanticGuardInit:
    """Tests for SemanticGuard initialization."""

    def test_default_threshold(self):
        """Test default threshold is set correctly."""
        guard = SemanticGuard()
        assert guard.threshold == DEFAULT_THRESHOLD

    def test_custom_threshold(self):
        """Test custom threshold is accepted."""
        guard = SemanticGuard(threshold=0.95)
        assert guard.threshold == 0.95

    def test_minimum_threshold(self):
        """Test minimum threshold is enforced."""
        guard = SemanticGuard(threshold=0.85)
        assert guard.threshold >= MIN_THRESHOLD

    def test_invalid_threshold_above_max(self):
        """Test threshold above 1.0 raises error."""
        with pytest.raises(ValueError):
            SemanticGuard(threshold=1.5)

    def test_invalid_threshold_below_min(self):
        """Test threshold below minimum raises error."""
        with pytest.raises(ValueError):
            SemanticGuard(threshold=0.5)


class TestSemanticGuardValidation:
    """Tests for validation methods."""

    def test_identical_texts_valid(self):
        """Test identical texts are valid."""
        guard = SemanticGuard()
        is_valid, sim = guard.validate("same text", "same text")
        assert is_valid is True
        assert sim == 1.0

    def test_similar_texts_valid(self):
        """Test similar texts are valid."""
        guard = SemanticGuard(threshold=0.80)
        is_valid, sim = guard.validate(
            "Write a Python function",
            "Write a Python function for testing"
        )
        assert 0.0 <= sim <= 1.0

    def test_different_texts_invalid(self):
        """Test very different texts are invalid."""
        guard = SemanticGuard(threshold=0.95)
        is_valid, sim = guard.validate(
            "Write a Python function",
            "What's the weather like?"
        )
        assert is_valid is False

    def test_compute_similarity_returns_float(self):
        """Test compute_similarity returns float."""
        guard = SemanticGuard()
        sim = guard.compute_similarity("test", "test")
        assert isinstance(sim, float)

    def test_empty_text_handled(self):
        """Test empty text is handled."""
        guard = SemanticGuard()
        sim = guard.compute_similarity("", "")
        assert isinstance(sim, float)


class TestSemanticGuardValidateOrRaise:
    """Tests for validate_or_raise method."""

    def test_valid_rewrite_returns_rewritten(self):
        """Test valid rewrite is returned."""
        guard = SemanticGuard(threshold=0.80)
        result = guard.validate_or_raise("same", "same")
        assert result == "same"

    def test_invalid_rewrite_raises(self):
        """Test invalid rewrite raises exception."""
        guard = SemanticGuard(threshold=0.99)
        with pytest.raises(SlimZeroSemanticRejection):
            guard.validate_or_raise(
                "Write a Python function to calculate sum",
                "Tell me a joke"
            )


class TestSemanticGuardProcess:
    """Tests for the process method."""

    def test_process_returns_stage_output(self):
        """Test process returns StageOutput."""
        guard = SemanticGuard()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=2)
        out = guard.process(inp)
        assert isinstance(out, StageOutput)

    def test_process_with_unchanged_prompt(self):
        """Test process with unchanged prompt."""
        guard = SemanticGuard()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=2)
        inp.metadata["original_prompt"] = "test"
        inp.metadata["rewritten_prompt"] = "test"
        out = guard.process(inp)
        assert out.modified is False

    def test_process_includes_validation_metadata(self):
        """Test process includes validation metadata."""
        guard = SemanticGuard()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=2)
        inp.metadata["original_prompt"] = "test"
        inp.metadata["rewritten_prompt"] = "test"
        out = guard.process(inp)
        assert "similarity" in out.metadata
        assert "threshold" in out.metadata
        assert "is_valid" in out.metadata

    def test_process_rejects_invalid_rewrite(self):
        """Test process rejects invalid rewrite."""
        guard = SemanticGuard(threshold=0.99)
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="original", intent=intent, token_count=2)
        inp.metadata["original_prompt"] = "Write a Python function"
        inp.metadata["rewritten_prompt"] = "Tell me a joke"
        out = guard.process(inp)
        assert out.prompt == "Write a Python function"


class TestSemanticGuardConstants:
    """Tests for constants."""

    def test_min_threshold_is_080(self):
        """Test minimum threshold is 0.80."""
        assert MIN_THRESHOLD == 0.80

    def test_default_threshold_is_092(self):
        """Test default threshold is 0.92."""
        assert DEFAULT_THRESHOLD == 0.92

    def test_min_below_default(self):
        """Test minimum is below default."""
        assert MIN_THRESHOLD < DEFAULT_THRESHOLD
