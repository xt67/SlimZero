"""
Tests for IntentExtractor stage (US-002)
"""

import pytest
from unittest.mock import patch

from slimzero.schemas import IntentSchema, StageInput, StageOutput, OutputFormat
from slimzero.stages.intent import IntentExtractor, OUTPUT_FORMAT_KEYWORDS, FILLER_PHRASES


class TestIntentExtractor:
    """Tests for IntentExtractor class."""

    def test_extractor_instantiation(self):
        """Test IntentExtractor can be instantiated."""
        extractor = IntentExtractor()
        assert extractor is not None

    def test_extractor_custom_model(self):
        """Test IntentExtractor with custom model."""
        extractor = IntentExtractor(model="en_core_web_md")
        assert extractor.model_name == "en_core_web_md"

    def test_extract_empty_prompt(self):
        """Test extraction with empty prompt."""
        extractor = IntentExtractor()
        result = extractor.extract("")
        assert result.core_task == ""
        assert result.raw_prompt == ""

    def test_extract_none_prompt(self):
        """Test extraction with None prompt."""
        extractor = IntentExtractor()
        result = extractor.extract(None)
        assert result.core_task == ""

    def test_extract_code_format(self):
        """Test detection of code output format."""
        extractor = IntentExtractor()
        result = extractor.extract("Write a function to calculate sum")
        assert result.output_format == OutputFormat.CODE

    def test_extract_list_format(self):
        """Test detection of list output format."""
        extractor = IntentExtractor()
        result = extractor.extract("List all users in the database")
        assert result.output_format == OutputFormat.LIST

    def test_extract_explain_format(self):
        """Test detection of explain output format."""
        extractor = IntentExtractor()
        result = extractor.extract("Explain how caching works")
        assert result.output_format == OutputFormat.EXPLAIN

    def test_extract_table_format(self):
        """Test detection of table output format."""
        extractor = IntentExtractor()
        result = extractor.extract("Create a comparison table")
        assert result.output_format == OutputFormat.TABLE

    def test_extract_general_format(self):
        """Test detection of general output format."""
        extractor = IntentExtractor()
        result = extractor.extract("Hello, how are you?")
        assert result.output_format == OutputFormat.GENERAL

    def test_extract_preserves_raw_prompt(self):
        """Test that raw prompt is preserved."""
        extractor = IntentExtractor()
        prompt = "Please could you help me"
        result = extractor.extract(prompt)
        assert result.raw_prompt == prompt

    def test_extract_removes_filler_phrases(self):
        """Test that filler phrases are removed from core task."""
        extractor = IntentExtractor()
        result = extractor.extract("Please could you kindly explain this")
        assert "please" not in result.core_task.lower()
        assert "could you" not in result.core_task.lower()

    def test_extract_returns_intent_schema(self):
        """Test that extract returns IntentSchema."""
        extractor = IntentExtractor()
        result = extractor.extract("Test prompt")
        assert isinstance(result, IntentSchema)

    def test_extract_intent_serializable(self):
        """Test that IntentSchema is serializable."""
        extractor = IntentExtractor()
        result = extractor.extract("Test prompt")
        data = result.to_dict()
        assert isinstance(data, dict)
        assert "core_task" in data


class TestIntentExtractorProcess:
    """Tests for the process method."""

    def test_process_returns_stage_output(self):
        """Test process returns StageOutput."""
        extractor = IntentExtractor()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test prompt", intent=intent, token_count=2)
        out = extractor.process(inp)
        assert isinstance(out, StageOutput)

    def test_process_passes_prompt_unchanged(self):
        """Test process passes prompt unchanged."""
        extractor = IntentExtractor()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="original prompt", intent=intent, token_count=3)
        out = extractor.process(inp)
        assert out.prompt == inp.prompt

    def test_process_includes_intent_in_metadata(self):
        """Test process includes intent in metadata."""
        extractor = IntentExtractor()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=2)
        out = extractor.process(inp)
        assert "intent" in out.metadata

    def test_process_has_notes(self):
        """Test process has notes about extraction."""
        extractor = IntentExtractor()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=2)
        out = extractor.process(inp)
        assert len(out.notes) > 0


class TestIntentExtractorOutputFormatDetection:
    """Tests for output format detection."""

    @pytest.mark.parametrize("prompt,expected", [
        ("Write a function to calculate sum", OutputFormat.CODE),
        ("Create a class for handling requests", OutputFormat.CODE),
        ("Show me how to implement this", OutputFormat.CODE),
        ("List all users in the database", OutputFormat.LIST),
        ("Give me bullet points of the features", OutputFormat.LIST),
        ("Create a comparison table", OutputFormat.TABLE),
        ("Make a spreadsheet of prices", OutputFormat.TABLE),
        ("Explain how caching works", OutputFormat.EXPLAIN),
        ("Describe the architecture", OutputFormat.EXPLAIN),
        ("What is a closure in programming", OutputFormat.EXPLAIN),
        ("Hello, how are you?", OutputFormat.GENERAL),
        ("Tell me about Python", OutputFormat.GENERAL),
    ])
    def test_format_detection(self, prompt, expected):
        """Test output format detection for various prompts."""
        extractor = IntentExtractor()
        result = extractor.extract(prompt)
        assert result.output_format == expected
