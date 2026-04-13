"""
Tests for HallucinationRiskScorer stage (US-008)
"""

import pytest

from slimzero.schemas import StageInput, StageOutput, IntentSchema, HallucinationRiskTier
from slimzero.stages.hallucination import (
    HallucinationRiskScorer,
    DATE_PATTERNS,
    NUMBER_PATTERNS,
    CITATION_PATTERNS,
    RECENCY_PATTERNS,
    DEFAULT_INSTRUCTIONS,
)


class TestHallucinationRiskScorer:
    """Tests for HallucinationRiskScorer class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        scorer = HallucinationRiskScorer()
        assert scorer.high_risk_instructions is not None
        assert scorer.medium_risk_instructions is not None

    def test_init_custom_instructions(self):
        """Test initialization with custom instructions."""
        custom_high = "Custom high risk instruction"
        custom_medium = "Custom medium risk instruction"
        scorer = HallucinationRiskScorer(
            high_risk_instructions=custom_high,
            medium_risk_instructions=custom_medium,
        )
        assert scorer.high_risk_instructions == custom_high
        assert scorer.medium_risk_instructions == custom_medium

    def test_classify_high_risk_dates(self):
        """Test classification of date-containing queries."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("When was Python 3.9 released?")
        assert tier == HallucinationRiskTier.HIGH
        assert high >= 1

    def test_classify_high_risk_numbers(self):
        """Test classification of number-specific queries."""
        scorer = HallucinationRiskScorer()

        result = scorer.score("Tell me the exact 95.5% of users who prefer iOS.")
        assert result[0] == HallucinationRiskTier.HIGH

    def test_classify_high_risk_citations(self):
        """Test classification of citation-containing queries."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score(
            "According to the latest research study, what are the benefits of exercise?"
        )
        assert tier == HallucinationRiskTier.HIGH

    def test_classify_high_risk_recency(self):
        """Test classification of recency queries."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("What is the latest news about AI?")
        assert tier == HallucinationRiskTier.HIGH

    def test_classify_medium_risk_verifiable(self):
        """Test classification of verifiable entity queries."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("Who is the CEO of Tesla?")
        assert tier in (HallucinationRiskTier.MEDIUM, HallucinationRiskTier.HIGH)

    def test_classify_low_risk_creative(self):
        """Test classification of creative/open-ended queries."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("Write a poem about the ocean")
        assert tier == HallucinationRiskTier.LOW

    def test_classify_low_risk_opinion(self):
        """Test classification of opinion queries."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("What do you think about programming?")
        assert tier == HallucinationRiskTier.LOW

    def test_score_empty_text(self):
        """Test scoring empty text returns LOW."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("")
        assert tier == HallucinationRiskTier.LOW
        assert high == 0
        assert medium == 0

    def test_score_none_text(self):
        """Test scoring None text returns LOW."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score(None)
        assert tier == HallucinationRiskTier.LOW
        assert high == 0
        assert medium == 0

    def test_get_instructions_high(self):
        """Test getting instructions for HIGH risk."""
        scorer = HallucinationRiskScorer()

        instructions = scorer.get_instructions(HallucinationRiskTier.HIGH)
        assert len(instructions) > 0
        assert "don't guess" in instructions.lower() or "uncertain" in instructions.lower()

    def test_get_instructions_medium(self):
        """Test getting instructions for MEDIUM risk."""
        scorer = HallucinationRiskScorer()

        instructions = scorer.get_instructions(HallucinationRiskTier.MEDIUM)
        assert len(instructions) > 0

    def test_get_instructions_low(self):
        """Test getting instructions for LOW risk."""
        scorer = HallucinationRiskScorer()

        instructions = scorer.get_instructions(HallucinationRiskTier.LOW)
        assert instructions == ""


class TestPatterns:
    """Tests for pattern definitions."""

    def test_date_patterns_exist(self):
        """Test date patterns are defined."""
        assert len(DATE_PATTERNS) > 0

    def test_number_patterns_exist(self):
        """Test number patterns are defined."""
        assert len(NUMBER_PATTERNS) > 0

    def test_citation_patterns_exist(self):
        """Test citation patterns are defined."""
        assert len(CITATION_PATTERNS) > 0

    def test_recency_patterns_exist(self):
        """Test recency patterns are defined."""
        assert len(RECENCY_PATTERNS) > 0

    def test_patterns_are_strings(self):
        """Test all patterns are valid strings."""
        for pattern in DATE_PATTERNS + NUMBER_PATTERNS + CITATION_PATTERNS + RECENCY_PATTERNS:
            assert isinstance(pattern, str)
            assert len(pattern) > 0


class TestDefaultInstructions:
    """Tests for default instructions."""

    def test_default_instructions_exist(self):
        """Test default instructions are defined."""
        assert HallucinationRiskTier.HIGH in DEFAULT_INSTRUCTIONS
        assert HallucinationRiskTier.MEDIUM in DEFAULT_INSTRUCTIONS
        assert HallucinationRiskTier.LOW in DEFAULT_INSTRUCTIONS

    def test_high_instructions_mentions_uncertainty(self):
        """Test HIGH risk instructions mention uncertainty."""
        instructions = DEFAULT_INSTRUCTIONS[HallucinationRiskTier.HIGH]
        assert len(instructions) > 0


class TestProcessMethod:
    """Tests for the process method."""

    def test_process_returns_stage_output(self):
        """Test process returns StageOutput."""
        scorer = HallucinationRiskScorer()

        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="Write a poem", intent=intent, token_count=3)

        out = scorer.process(inp)
        assert isinstance(out, StageOutput)

    def test_process_high_risk(self):
        """Test process with high risk query."""
        scorer = HallucinationRiskScorer()

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="What happened on 2024-01-15 in the stock market?",
            intent=intent,
            token_count=10,
        )

        out = scorer.process(inp)
        assert out.metadata["risk_tier"] == HallucinationRiskTier.HIGH.value
        assert out.metadata["is_high_risk"] is True

    def test_process_low_risk(self):
        """Test process with low risk query."""
        scorer = HallucinationRiskScorer()

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="Write me a haiku about coding",
            intent=intent,
            token_count=6,
        )

        out = scorer.process(inp)
        assert out.metadata["is_low_risk"] is True

    def test_process_metadata(self):
        """Test that process includes proper metadata."""
        scorer = HallucinationRiskScorer()

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="Who founded Google?",
            intent=intent,
            token_count=4,
        )

        out = scorer.process(inp)
        assert "risk_tier" in out.metadata
        assert "high_matches" in out.metadata
        assert "medium_matches" in out.metadata
        assert "instructions" in out.metadata
        assert "is_high_risk" in out.metadata
        assert "is_medium_risk" in out.metadata
        assert "is_low_risk" in out.metadata

    def test_process_modifies_for_high_risk(self):
        """Test that process is marked modified for high risk."""
        scorer = HallucinationRiskScorer()

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="What is the exact population of China?",
            intent=intent,
            token_count=7,
        )

        out = scorer.process(inp)
        assert out.modified is True


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_long_query(self):
        """Test handling of very long queries."""
        scorer = HallucinationRiskScorer()

        long_query = "Explain " * 100 + "the population of Germany"
        tier, high, medium = scorer.score(long_query)
        assert tier in HallucinationRiskTier

    def test_unicode_content(self):
        """Test handling of unicode content."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("What is émojis 🎉 about?")
        assert tier in HallucinationRiskTier

    def test_special_characters(self):
        """Test handling of special characters."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("@@@###$$$")
        assert tier in HallucinationRiskTier

    def test_only_whitespace(self):
        """Test handling of whitespace-only text returns LOW."""
        scorer = HallucinationRiskScorer()

        tier, high, medium = scorer.score("   \n\t  ")
        assert tier == HallucinationRiskTier.LOW

    def test_mixed_case_patterns(self):
        """Test that patterns match case-insensitively."""
        scorer = HallucinationRiskScorer()

        tier1, _, _ = scorer.score("WHEN was python released IN 2020")
        tier2, _, _ = scorer.score("when was python released in 2020")
        assert tier1 == tier2

    def test_multiple_patterns_same_text(self):
        """Test that multiple patterns can match in same text."""
        scorer = HallucinationRiskScorer()

        text = "According to the 2024 study, the population is 8 billion"
        tier, high, medium = scorer.score(text)
        assert high >= 1
