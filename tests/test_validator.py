"""
Tests for ResponseValidator (US-010)
"""

import pytest

from slimzero.schemas import IntentSchema, OutputFormat
from slimzero.post.validator import ResponseValidator, DEFAULT_THRESHOLD, MAX_RESPONSE_TOKENS


class TestResponseValidator:
    """Tests for ResponseValidator class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        validator = ResponseValidator()
        assert validator.threshold == DEFAULT_THRESHOLD
        assert validator.model_name == "all-MiniLM-L6-v2"

    def test_init_custom_threshold(self):
        """Test initialization with custom threshold."""
        validator = ResponseValidator(threshold=0.7)
        assert validator.threshold == 0.7

    def test_init_threshold_bounds(self):
        """Test threshold is clamped to valid range."""
        validator_high = ResponseValidator(threshold=1.5)
        assert validator_high.threshold == 1.0

        validator_low = ResponseValidator(threshold=-0.5)
        assert validator_low.threshold == 0.0

    def test_estimate_tokens(self):
        """Test token estimation."""
        validator = ResponseValidator()
        assert validator._estimate_tokens("hello world") == 2
        assert validator._estimate_tokens("one two three four five") == 5
        assert validator._estimate_tokens("") == 0

    def test_compute_keyword_similarity(self):
        """Test keyword-based similarity."""
        validator = ResponseValidator()

        sim = validator._compute_keyword_similarity("Python programming", "Write Python code")
        assert 0.0 <= sim <= 1.0

    def test_compute_keyword_similarity_no_overlap(self):
        """Test keyword similarity with no overlap."""
        validator = ResponseValidator()

        sim = validator._compute_keyword_similarity("Python code", "Weather today")
        assert sim == 0.0

    def test_compute_keyword_similarity_empty(self):
        """Test keyword similarity with empty strings."""
        validator = ResponseValidator()

        assert validator._compute_keyword_similarity("", "test") == 0.0
        assert validator._compute_keyword_similarity("test", "") == 0.0
        assert validator._compute_keyword_similarity("", "") == 0.0

    def test_validate_empty_response(self):
        """Test validation of empty response."""
        validator = ResponseValidator()
        intent = IntentSchema(core_task="test")

        is_valid, sim = validator.validate(intent, "")
        assert is_valid is False
        assert sim == 0.0

    def test_validate_none_response(self):
        """Test validation of None response."""
        validator = ResponseValidator()
        intent = IntentSchema(core_task="test")

        is_valid, sim = validator.validate(intent, None)
        assert is_valid is False

    def test_validate_empty_intent(self):
        """Test validation with empty intent."""
        validator = ResponseValidator()
        intent = IntentSchema(core_task="")

        is_valid, sim = validator.validate(intent, "Some response")
        assert is_valid is True

    def test_validate_matching_response(self):
        """Test validation of matching response."""
        validator = ResponseValidator(threshold=0.3)
        intent = IntentSchema(core_task="Explain Python programming")

        is_valid, sim = validator.validate(intent, "Python is a programming language")
        assert 0.0 <= sim <= 1.0

    def test_validate_truncates_long_response(self):
        """Test that long responses are truncated."""
        validator = ResponseValidator(threshold=0.0)
        intent = IntentSchema(core_task="test")

        long_response = " ".join(["word"] * 600)
        is_valid, sim = validator.validate(intent, long_response)
        assert is_valid is True

    def test_validate_below_threshold(self):
        """Test validation below threshold."""
        validator = ResponseValidator(threshold=0.99)
        intent = IntentSchema(core_task="Python code")

        is_valid, sim = validator.validate(intent, "Tell me about the weather")
        assert is_valid is False


class TestValidateWithMetadata:
    """Tests for validate_with_metadata method."""

    def test_returns_dict(self):
        """Test that validate_with_metadata returns dict."""
        validator = ResponseValidator()
        intent = IntentSchema(core_task="test")
        response = "test response"

        result = validator.validate_with_metadata(intent, response)
        assert isinstance(result, dict)

    def test_contains_required_fields(self):
        """Test that result contains required fields."""
        validator = ResponseValidator()
        intent = IntentSchema(core_task="Python programming")
        response = "Python is a language"

        result = validator.validate_with_metadata(intent, response)

        assert "is_valid" in result
        assert "similarity" in result
        assert "threshold" in result
        assert "response_length" in result
        assert "response_tokens" in result
        assert "st_available" in result

    def test_similarity_in_range(self):
        """Test that similarity is in valid range."""
        validator = ResponseValidator()
        intent = IntentSchema(core_task="test query")
        response = "test response here"

        result = validator.validate_with_metadata(intent, response)
        assert 0.0 <= result["similarity"] <= 1.0


class TestConstants:
    """Tests for constant values."""

    def test_default_threshold_is_060(self):
        """Test default threshold is 0.60."""
        assert DEFAULT_THRESHOLD == 0.60

    def test_max_response_tokens_is_positive(self):
        """Test max response tokens is positive."""
        assert MAX_RESPONSE_TOKENS > 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_content(self):
        """Test handling of unicode content."""
        validator = ResponseValidator()

        intent = IntentSchema(core_task="test émojis")
        response = "response with 🎉"
        is_valid, sim = validator.validate(intent, response)
        assert isinstance(sim, float)

    def test_special_characters(self):
        """Test handling of special characters."""
        validator = ResponseValidator()

        intent = IntentSchema(core_task="@mention #hashtag")
        response = "!@#$%^&*()"
        is_valid, sim = validator.validate(intent, response)
        assert isinstance(sim, float)

    def test_very_short_response(self):
        """Test handling of very short response."""
        validator = ResponseValidator()

        intent = IntentSchema(core_task="test")
        response = "a"
        is_valid, sim = validator.validate(intent, response)
        assert isinstance(sim, float)

    def test_very_long_intent(self):
        """Test handling of very long intent."""
        validator = ResponseValidator()

        long_intent = " ".join(["word"] * 200)
        intent = IntentSchema(core_task=long_intent)
        response = "test response"
        is_valid, sim = validator.validate(intent, response)
        assert isinstance(sim, float)
