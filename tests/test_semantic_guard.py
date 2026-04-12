"""
Tests for Semantic Guard Stage (US-003)

Verifies that SemanticGuard correctly validates prompt rewrites.
"""

import pytest
from slimzero.schemas import StageInput, IntentSchema
from slimzero.stages.semantic_guard import SemanticGuard, MIN_THRESHOLD, DEFAULT_THRESHOLD
from slimzero.exceptions import SlimZeroSemanticRejection


class TestSemanticGuardInit:
    """Test SemanticGuard initialization."""

    def test_default_threshold(self):
        """Should use default threshold of 0.92."""
        guard = SemanticGuard()
        assert guard.threshold == DEFAULT_THRESHOLD

    def test_custom_threshold(self):
        """Should accept custom threshold."""
        guard = SemanticGuard(threshold=0.85)
        assert guard.threshold == 0.85

    def test_minimum_threshold(self):
        """Should accept minimum threshold of 0.80."""
        guard = SemanticGuard(threshold=MIN_THRESHOLD)
        assert guard.threshold == MIN_THRESHOLD

    def test_invalid_threshold_above_max(self):
        """Should reject threshold above 1.0."""
        with pytest.raises(ValueError):
            SemanticGuard(threshold=1.1)

    def test_invalid_threshold_below_min(self):
        """Should reject threshold below minimum."""
        with pytest.raises(ValueError):
            SemanticGuard(threshold=0.5)


class TestSemanticGuardValidation:
    """Test SemanticGuard validation logic."""

    def test_identical_texts_valid(self):
        """Identical texts should always be valid."""
        guard = SemanticGuard()
        is_valid, similarity = guard.validate("Hello world", "Hello world")
        assert is_valid is True
        assert similarity == 1.0

    def test_similar_texts_valid(self):
        """Similar texts should be valid."""
        guard = SemanticGuard(threshold=0.80)
        is_valid, similarity = guard.validate(
            "Explain how neural networks work",
            "Explain neural networks"
        )
        assert similarity > 0.5
        assert is_valid == (similarity >= 0.80)

    def test_different_texts_invalid(self):
        """Very different texts should be invalid at high threshold."""
        guard = SemanticGuard(threshold=0.92)
        is_valid, similarity = guard.validate(
            "Explain quantum physics",
            "Write a poem about cats"
        )
        assert similarity < 0.92
        assert is_valid is False

    def test_compute_similarity_returns_float(self):
        """compute_similarity should return float between 0 and 1."""
        guard = SemanticGuard()
        similarity = guard.compute_similarity("Hello", "Hi")
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_empty_text_handled(self):
        """Should handle empty strings."""
        guard = SemanticGuard()
        similarity = guard.compute_similarity("", "Some text")
        assert isinstance(similarity, float)


class TestSemanticGuardValidateOrRaise:
    """Test validate_or_raise method."""

    def test_valid_rewrite_returns_rewritten(self):
        """Valid rewrite should be returned."""
        guard = SemanticGuard(threshold=0.95)
        result = guard.validate_or_raise(
            "Explain machine learning",
            "Explain machine learning"
        )
        assert result == "Explain machine learning"

    def test_invalid_rewrite_raises(self):
        """Invalid rewrite should raise SlimZeroSemanticRejection."""
        guard = SemanticGuard(threshold=0.99)
        with pytest.raises(SlimZeroSemanticRejection) as exc_info:
            guard.validate_or_raise(
                "Explain quantum physics in detail",
                "Write a recipe for cake"
            )
        assert exc_info.value.similarity is not None
        assert exc_info.value.threshold == 0.99


class TestSemanticGuardProcess:
    """Test SemanticGuard.process method."""

    def test_process_returns_stage_output(self):
        """process() should return StageOutput."""
        from slimzero.schemas import StageOutput
        guard = SemanticGuard()
        inp = StageInput(
            prompt="Explain ML",
            intent=IntentSchema(core_task="test"),
            token_count=5,
            metadata={"original_prompt": "Explain machine learning"},
        )
        out = guard.process(inp)
        assert isinstance(out, StageOutput)

    def test_process_with_unchanged_prompt(self):
        """process() should handle unchanged prompt."""
        guard = SemanticGuard()
        inp = StageInput(
            prompt="Same prompt",
            intent=IntentSchema(core_task="test"),
            token_count=5,
        )
        out = guard.process(inp)
        assert out.prompt == "Same prompt"
        assert out.metadata["similarity"] == 1.0

    def test_process_includes_validation_metadata(self):
        """process() should include validation metadata."""
        guard = SemanticGuard(threshold=0.85)
        inp = StageInput(
            prompt="Rewritten",
            intent=IntentSchema(core_task="test"),
            token_count=5,
            metadata={
                "original_prompt": "Original text",
                "rewritten_prompt": "Rewritten text",
            },
        )
        out = guard.process(inp)
        assert "similarity" in out.metadata
        assert "threshold" in out.metadata
        assert "is_valid" in out.metadata
        assert "st_available" in out.metadata

    def test_process_rejects_invalid_rewrite(self):
        """process() should return original prompt for invalid rewrite."""
        guard = SemanticGuard(threshold=0.99)
        inp = StageInput(
            prompt="Completely different text",
            intent=IntentSchema(core_task="test"),
            token_count=5,
            metadata={
                "original_prompt": "Explain neural networks deeply",
                "rewritten_prompt": "Write about cooking",
            },
        )
        out = guard.process(inp)
        assert out.prompt == "Explain neural networks deeply"
        assert out.metadata["is_valid"] is False


class TestSemanticGuardConstants:
    """Test SemanticGuard constants."""

    def test_min_threshold_is_080(self):
        """MIN_THRESHOLD should be 0.80."""
        assert MIN_THRESHOLD == 0.80

    def test_default_threshold_is_092(self):
        """DEFAULT_THRESHOLD should be 0.92."""
        assert DEFAULT_THRESHOLD == 0.92

    def test_min_below_default(self):
        """MIN_THRESHOLD should be less than DEFAULT_THRESHOLD."""
        assert MIN_THRESHOLD < DEFAULT_THRESHOLD
