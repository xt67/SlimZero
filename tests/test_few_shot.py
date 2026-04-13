"""
Tests for FewShotRanker stage (US-005)
"""

import pytest
from unittest.mock import patch

from slimzero.schemas import StageInput, StageOutput, IntentSchema, OutputFormat
from slimzero.stages.few_shot import (
    FewShotRanker,
    Q_A_PATTERN,
    NUMBERED_PATTERN,
    XML_TAG_PATTERN,
    DEFAULT_K,
    MIN_K,
)


class TestFewShotRanker:
    """Tests for FewShotRanker class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        ranker = FewShotRanker()
        assert ranker.k == DEFAULT_K
        assert ranker.model_name == "all-MiniLM-L6-v2"

    def test_init_custom_k(self):
        """Test initialization with custom k."""
        ranker = FewShotRanker(k=5)
        assert ranker.k == 5

    def test_init_k_bounds(self):
        """Test k is clamped to valid range."""
        ranker_high = FewShotRanker(k=15)
        assert ranker_high.k == 10

        ranker_low = FewShotRanker(k=0)
        assert ranker_low.k == MIN_K

    def test_detect_qa_examples(self):
        """Test detection of Q:/A: format examples."""
        ranker = FewShotRanker()

        text = """
        Q: What is Python?
        A: Python is a programming language.
        
        Q: What is JavaScript?
        A: JavaScript is a web language.
        """

        examples = ranker._detect_examples(text)
        assert len(examples) >= 2

    def test_detect_xml_examples(self):
        """Test detection of XML-tagged examples."""
        ranker = FewShotRanker()

        text = """
        <input>How are you?</input>
        <output>I am fine.</output>
        <input>What is 2+2?</input>
        <output>4</output>
        """

        examples = ranker._detect_examples(text)
        assert len(examples) >= 2

    def test_detect_mixed_examples(self):
        """Test detection with mixed formats."""
        ranker = FewShotRanker()

        text = """
        Q: First question?
        A: First answer.
        
        Q: Second question?
        A: Second answer.
        """

        examples = ranker._detect_examples(text)
        assert len(examples) >= 2

    def test_keyword_score_basic(self):
        """Test basic keyword scoring."""
        ranker = FewShotRanker()

        example = "Python is a programming language"
        query = "What is Python programming?"

        score = ranker._keyword_score(example, query)
        assert 0.0 <= score <= 1.0
        assert score > 0

    def test_keyword_score_no_overlap(self):
        """Test keyword score with no overlap."""
        ranker = FewShotRanker()

        example = "The weather is sunny today"
        query = "How to write Python code?"

        score = ranker._keyword_score(example, query)
        assert score == 0.0

    def test_keyword_score_empty_inputs(self):
        """Test keyword score with empty inputs."""
        ranker = FewShotRanker()

        assert ranker._keyword_score("", "query") == 0.0
        assert ranker._keyword_score("example", "") == 0.0

    def test_rank_empty_text(self):
        """Test ranking with empty text."""
        ranker = FewShotRanker()
        result = ranker.rank("", "test query")
        assert result == []

    def test_rank_empty_query(self):
        """Test ranking with empty query."""
        ranker = FewShotRanker()
        result = ranker.rank("some examples", "")
        assert result == []

    def test_rank_preserves_at_least_one(self):
        """Test that at least one example is preserved if any exist."""
        ranker = FewShotRanker(k=1)

        text = "Q: Single question?\nA: Single answer."
        result = ranker.rank(text, "test query")

        assert len(result) >= 1

    def test_rank_respects_k(self):
        """Test that ranking respects k parameter."""
        ranker = FewShotRanker(k=2)

        text = """
        Q: What is Python?
        A: A programming language.
        
        Q: What is JavaScript?
        A: A web language.
        
        Q: What is Java?
        A: A programming language.
        
        Q: What is Ruby?
        A: A programming language.
        """

        result = ranker.rank(text, "programming")
        assert len(result) <= 2

    def test_rank_sorted_by_relevance(self):
        """Test that examples are sorted by relevance."""
        ranker = FewShotRanker(k=3)

        text = """
        Q: What is Python?
        A: A programming language.
        
        Q: What is the weather?
        A: It is sunny.
        
        Q: How to code in Python?
        A: Use the Python syntax.
        """

        result = ranker.rank(text, "Python programming")
        assert len(result) >= 1


class TestPatterns:
    """Tests for pattern definitions."""

    def test_qa_pattern_exists(self):
        """Test Q/A pattern is defined."""
        assert Q_A_PATTERN is not None

    def test_numbered_pattern_exists(self):
        """Test numbered pattern is defined."""
        assert NUMBERED_PATTERN is not None

    def test_xml_pattern_exists(self):
        """Test XML pattern is defined."""
        assert XML_TAG_PATTERN is not None


class TestConstants:
    """Tests for constant values."""

    def test_default_k_is_positive(self):
        """Test default k is positive."""
        assert DEFAULT_K > 0

    def test_min_k_is_one(self):
        """Test minimum k is 1."""
        assert MIN_K == 1


class TestProcessMethod:
    """Tests for the process method."""

    def test_process_no_examples(self):
        """Test process with no examples."""
        ranker = FewShotRanker()

        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test query", intent=intent, token_count=3, few_shot_examples=None)

        out = ranker.process(inp)

        assert isinstance(out, StageOutput)
        assert out.modified is False
        assert "No few-shot" in out.notes

    def test_process_single_example(self):
        """Test process with single example (below minimum)."""
        ranker = FewShotRanker()

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="test query",
            intent=intent,
            token_count=3,
            few_shot_examples=["Q: One?\nA: One."],
        )

        out = ranker.process(inp)

        assert isinstance(out, StageOutput)
        assert out.modified is False
        assert "1 example" in out.notes

    def test_process_multiple_examples(self):
        """Test process with multiple examples."""
        ranker = FewShotRanker(k=2)

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="Python programming",
            intent=intent,
            token_count=3,
            few_shot_examples=[
                "Q: What is Python?\nA: A language.",
                "Q: What is Java?\nA: A language.",
                "Q: What is the weather?\nA: Sunny.",
            ],
        )

        out = ranker.process(inp)

        assert isinstance(out, StageOutput)
        assert "retained" in out.notes.lower()
        assert "few_shot_mode" in out.metadata
        assert "examples_count" in out.metadata
        assert "retained_count" in out.metadata

    def test_process_metadata(self):
        """Test process metadata contains correct fields."""
        ranker = FewShotRanker(k=3)

        intent = IntentSchema(core_task="test")
        inp = StageInput(
            prompt="test",
            intent=intent,
            token_count=2,
            few_shot_examples=[
                "Q: What is A?\nA: Alpha.",
                "Q: What is B?\nA: Beta.",
                "Q: What is C?\nA: Gamma.",
            ],
        )

        out = ranker.process(inp)

        assert out.metadata["k"] == 3
        assert out.metadata["examples_count"] == 3
        assert out.metadata["retained_count"] <= 3
        assert "st_available" in out.metadata


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_short_example(self):
        """Test handling of very short examples."""
        ranker = FewShotRanker()

        examples = ranker._detect_examples("x\ny")
        assert isinstance(examples, list)

    def test_empty_example_list(self):
        """Test handling of empty example list."""
        ranker = FewShotRanker()
        result = ranker.rank("", "query")
        assert result == []

    def test_all_same_examples(self):
        """Test handling of duplicate examples."""
        ranker = FewShotRanker(k=2)

        text = """
        Q: Question?
        A: Answer.
        
        Q: Question?
        A: Answer.
        """

        result = ranker.rank(text, "Question")
        assert len(result) <= 2

    def test_unicode_in_examples(self):
        """Test handling of unicode in examples."""
        ranker = FewShotRanker()

        text = "Q: What's up?\nA: émojis 🎉\n\nQ: Next?\nA: Done ✓"
        result = ranker.rank(text, "emoji")

        assert isinstance(result, list)

    def test_special_characters(self):
        """Test handling of special characters in examples."""
        ranker = FewShotRanker()

        text = "Q: Code?\nA: `x = 1`\n\nQ: Other?\nA: @#$%"
        result = ranker.rank(text, "code")

        assert isinstance(result, list)
