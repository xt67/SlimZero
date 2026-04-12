"""
Tests for Intent Extractor Stage (US-002)

Verifies that IntentExtractor correctly parses user prompts.
"""

import pytest
from slimzero.schemas import StageInput, IntentSchema, OutputFormat
from slimzero.stages.intent import IntentExtractor


class TestIntentExtractor:
    """Test IntentExtractor class."""

    def test_extractor_instantiation(self):
        """IntentExtractor should be instantiable."""
        extractor = IntentExtractor()
        assert extractor is not None
        assert extractor.model_name == "en_core_web_sm"

    def test_extractor_custom_model(self):
        """IntentExtractor should accept custom model name."""
        extractor = IntentExtractor(model="en_core_web_md")
        assert extractor.model_name == "en_core_web_md"

    def test_extract_empty_prompt(self):
        """Should handle empty prompt gracefully."""
        extractor = IntentExtractor()
        intent = extractor.extract("")
        assert intent.core_task == ""
        assert intent.output_format == OutputFormat.UNKNOWN
        assert intent.raw_prompt == ""

    def test_extract_none_prompt(self):
        """Should handle None prompt gracefully."""
        extractor = IntentExtractor()
        intent = extractor.extract(None)
        assert intent.core_task == ""
        assert intent.output_format == OutputFormat.UNKNOWN

    def test_extract_code_format(self):
        """Should detect code output format."""
        extractor = IntentExtractor()
        intent = extractor.extract("Write a Python function to calculate sum")
        assert intent.output_format == OutputFormat.CODE

    def test_extract_list_format(self):
        """Should detect list output format."""
        extractor = IntentExtractor()
        intent = extractor.extract("List all the files in the directory")
        assert intent.output_format == OutputFormat.LIST

    def test_extract_explain_format(self):
        """Should detect explain output format."""
        extractor = IntentExtractor()
        intent = extractor.extract("Explain how neural networks work")
        assert intent.output_format == OutputFormat.EXPLAIN

    def test_extract_table_format(self):
        """Should detect table output format."""
        extractor = IntentExtractor()
        intent = extractor.extract("Create a table comparing Python and JavaScript")
        assert intent.output_format == OutputFormat.TABLE

    def test_extract_general_format(self):
        """Should default to general format."""
        extractor = IntentExtractor()
        intent = extractor.extract("Run the analysis")
        assert intent.output_format == OutputFormat.GENERAL

    def test_extract_preserves_raw_prompt(self):
        """Should preserve original prompt in raw_prompt."""
        original = "Please explain machine learning"
        extractor = IntentExtractor()
        intent = extractor.extract(original)
        assert intent.raw_prompt == original

    def test_extract_removes_filler_phrases(self):
        """Should remove filler phrases from core_task."""
        extractor = IntentExtractor()
        intent = extractor.extract("Can you please explain machine learning")
        assert "please" not in intent.core_task.lower()
        assert "can you" not in intent.core_task.lower()

    def test_extract_returns_intent_schema(self):
        """Should return IntentSchema instance."""
        extractor = IntentExtractor()
        intent = extractor.extract("Explain neural networks")
        assert isinstance(intent, IntentSchema)

    def test_extract_intent_serializable(self):
        """Intent should be convertible to dict."""
        extractor = IntentExtractor()
        intent = extractor.extract("Explain neural networks")
        d = intent.to_dict()
        assert "core_task" in d
        assert "output_format" in d
        assert isinstance(d["entities"], list)


class TestIntentExtractorProcess:
    """Test IntentExtractor.process method."""

    def test_process_returns_stage_output(self):
        """process() should return StageOutput."""
        from slimzero.schemas import StageOutput
        extractor = IntentExtractor()
        inp = StageInput(
            prompt="Write Python code",
            intent=IntentSchema(core_task="test"),
            token_count=10,
        )
        out = extractor.process(inp)
        assert isinstance(out, StageOutput)

    def test_process_passes_prompt_unchanged(self):
        """process() should pass prompt unchanged."""
        extractor = IntentExtractor()
        original = "Write Python code"
        inp = StageInput(
            prompt=original,
            intent=IntentSchema(core_task="test"),
            token_count=10,
        )
        out = extractor.process(inp)
        assert out.prompt == original
        assert out.modified is False

    def test_process_includes_intent_in_metadata(self):
        """process() should include intent in metadata."""
        extractor = IntentExtractor()
        inp = StageInput(
            prompt="Explain ML",
            intent=IntentSchema(core_task="test"),
            token_count=5,
        )
        out = extractor.process(inp)
        assert "intent" in out.metadata
        assert "spacy_available" in out.metadata

    def test_process_has_notes(self):
        """process() should include notes."""
        extractor = IntentExtractor()
        inp = StageInput(
            prompt="Explain machine learning",
            intent=IntentSchema(core_task="test"),
            token_count=5,
        )
        out = extractor.process(inp)
        assert out.notes is not None
        assert len(out.notes) > 0


class TestIntentExtractorOutputFormatDetection:
    """Test output format detection."""

    @pytest.mark.parametrize("prompt,expected_format", [
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
    def test_format_detection(self, prompt, expected_format):
        """Should correctly detect output formats."""
        extractor = IntentExtractor()
        intent = extractor.extract(prompt)
        assert intent.output_format == expected_format
