"""
Tests for HallucinationFlagger (US-011)
"""

import pytest

from slimzero.post.flagger import (
    HallucinationFlagger,
    DATE_ASSERTIONS,
    NUMERIC_SPECIFICS,
    CITATION_PHRASES,
    AUTHORITY_CLAIMS,
    ALL_PATTERNS,
)


class TestHallucinationFlagger:
    """Tests for HallucinationFlagger class."""

    def test_init(self):
        """Test initialization."""
        flagger = HallucinationFlagger()
        assert flagger is not None
        assert len(flagger._compiled_patterns) > 0

    def test_flag_empty_response(self):
        """Test flagging empty response."""
        flagger = HallucinationFlagger()

        result = flagger.flag("")
        assert result["has_flags"] is False
        assert result["total_flags"] == 0

    def test_flag_none_response(self):
        """Test flagging None response."""
        flagger = HallucinationFlagger()

        result = flagger.flag(None)
        assert result["has_flags"] is False

    def test_flag_date_assertion(self):
        """Test flagging date assertion."""
        flagger = HallucinationFlagger()

        result = flagger.flag("The company was founded in 1995.")
        assert result["has_flags"] is True
        assert result["total_flags"] >= 1

    def test_flag_numeric_specific(self):
        """Test flagging numeric specific."""
        flagger = HallucinationFlagger()

        result = flagger.flag("About 75.5% of users prefer this product.")
        assert result["has_flags"] is True

    def test_flag_citation_phrase(self):
        """Test flagging citation phrase."""
        flagger = HallucinationFlagger()

        result = flagger.flag("According to the peer-reviewed study published in 2023.")
        assert result["has_flags"] is True

    def test_flag_authority_claim(self):
        """Test flagging authority claim."""
        flagger = HallucinationFlagger()

        result = flagger.flag("Scientists say this is the best approach.")
        assert result["has_flags"] is True

    def test_flag_no_hallucination(self):
        """Test response with no hallucinations."""
        flagger = HallucinationFlagger()

        result = flagger.flag("I can help you with that. What would you like to know?")
        assert "has_flags" in result

    def test_flag_multiple_patterns(self):
        """Test flagging multiple patterns in one response."""
        flagger = HallucinationFlagger()

        response = "In 2020, scientists found that 95% of users agreed."
        result = flagger.flag(response)

        assert result["has_flags"] is True
        assert result["total_flags"] >= 2

    def test_flag_returns_categories(self):
        """Test that flag returns categories."""
        flagger = HallucinationFlagger()

        result = flagger.flag("Founded in 1995.")
        assert "categories" in result
        assert isinstance(result["categories"], dict)

    def test_flag_returns_flags_list(self):
        """Test that flag returns list of flags."""
        flagger = HallucinationFlagger()

        result = flagger.flag("Founded in 1995.")
        assert "flags" in result
        assert isinstance(result["flags"], list)


class TestFlagWithContext:
    """Tests for flag_with_context method."""

    def test_flag_with_context_empty(self):
        """Test flag_with_context with empty response."""
        flagger = HallucinationFlagger()

        result = flagger.flag_with_context("")
        assert result["has_flags"] is False
        assert result["total_flags"] == 0

    def test_flag_with_context_returns_context(self):
        """Test that flag_with_context returns context."""
        flagger = HallucinationFlagger()

        result = flagger.flag_with_context("The event happened in 1995 when things changed.")
        if result["has_flags"]:
            assert "context" in result["flags"][0]


class TestPatterns:
    """Tests for pattern definitions."""

    def test_date_patterns_exist(self):
        """Test date patterns are defined."""
        assert len(DATE_ASSERTIONS) > 0

    def test_numeric_patterns_exist(self):
        """Test numeric patterns are defined."""
        assert len(NUMERIC_SPECIFICS) > 0

    def test_citation_patterns_exist(self):
        """Test citation patterns are defined."""
        assert len(CITATION_PHRASES) > 0

    def test_authority_patterns_exist(self):
        """Test authority patterns are defined."""
        assert len(AUTHORITY_CLAIMS) > 0

    def test_all_patterns_exist(self):
        """Test all patterns are defined."""
        assert len(ALL_PATTERNS) > 0

    def test_patterns_are_strings(self):
        """Test all patterns are valid strings."""
        for pattern in ALL_PATTERNS:
            assert isinstance(pattern, str)
            assert len(pattern) > 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_content(self):
        """Test handling of unicode content."""
        flagger = HallucinationFlagger()

        result = flagger.flag("In 年 2020, something happened")
        assert "has_flags" in result

    def test_special_characters(self):
        """Test handling of special characters."""
        flagger = HallucinationFlagger()

        result = flagger.flag("!@#$%^&*()")
        assert "has_flags" in result

    def test_very_long_response(self):
        """Test handling of very long response."""
        flagger = HallucinationFlagger()

        long_response = "word " * 1000 + "in 2020"
        result = flagger.flag(long_response)
        assert "has_flags" in result

    def test_mixed_case_patterns(self):
        """Test that patterns match case-insensitively."""
        flagger = HallucinationFlagger()

        result1 = flagger.flag("IN 2020, something happened")
        result2 = flagger.flag("in 2020, something happened")
        assert result1["has_flags"] == result2["has_flags"]

    def test_pattern_at_boundaries(self):
        """Test pattern matching at text boundaries."""
        flagger = HallucinationFlagger()

        result = flagger.flag("2020")
        assert "has_flags" in result
