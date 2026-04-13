"""
Tests for ResponseFormatInjector stage (US-007)
"""

import pytest

from slimzero.schemas import StageInput, StageOutput, IntentSchema, OutputFormat
from slimzero.stages.injector import (
    ResponseFormatInjector,
    FRAGMENT_LIBRARY,
    MAX_FRAGMENT_TOKENS,
)


class TestResponseFormatInjector:
    """Tests for ResponseFormatInjector class."""

    def test_init(self):
        """Test initialization."""
        injector = ResponseFormatInjector()
        assert injector is not None

    def test_estimate_tokens(self):
        """Test token estimation."""
        injector = ResponseFormatInjector()
        assert injector._estimate_tokens("hello world") == 2
        assert injector._estimate_tokens("one two three four five") == 5

    def test_has_response_instructions_empty(self):
        """Test detection with empty text."""
        injector = ResponseFormatInjector()
        assert injector._has_response_instructions("") is False
        assert injector._has_response_instructions(None) is False

    def test_has_response_instructions_concise(self):
        """Test detection of concise keyword."""
        injector = ResponseFormatInjector()
        assert injector._has_response_instructions("Please be concise") is True
        assert injector._has_response_instructions("Be concise") is True

    def test_has_response_instructions_brief(self):
        """Test detection of brief keyword."""
        injector = ResponseFormatInjector()
        assert injector._has_response_instructions("Explain briefly") is True

    def test_has_response_instructions_no_intro(self):
        """Test detection of no intro pattern."""
        injector = ResponseFormatInjector()
        assert injector._has_response_instructions("No preamble needed") is True
        assert injector._has_response_instructions("No explanation") is True

    def test_has_response_instructions_list_only(self):
        """Test detection of list only pattern."""
        injector = ResponseFormatInjector()
        assert injector._has_response_instructions("List only the items") is True

    def test_has_response_instructions_code_only(self):
        """Test detection of code only pattern."""
        injector = ResponseFormatInjector()
        assert injector._has_response_instructions("Code only") is True

    def test_has_response_instructions_negative(self):
        """Test no detection for normal text."""
        injector = ResponseFormatInjector()
        assert injector._has_response_instructions("You are a helpful assistant") is False
        assert injector._has_response_instructions("Explain how this works") is False

    def test_get_fragment_code(self):
        """Test getting fragment for CODE format."""
        injector = ResponseFormatInjector()
        fragment = injector._get_fragment(OutputFormat.CODE)
        assert "code" in fragment.lower() or "output" in fragment.lower()
        assert injector._estimate_tokens(fragment) <= MAX_FRAGMENT_TOKENS

    def test_get_fragment_list(self):
        """Test getting fragment for LIST format."""
        injector = ResponseFormatInjector()
        fragment = injector._get_fragment(OutputFormat.LIST)
        assert "list" in fragment.lower()
        assert injector._estimate_tokens(fragment) <= MAX_FRAGMENT_TOKENS

    def test_get_fragment_explain(self):
        """Test getting fragment for EXPLAIN format."""
        injector = ResponseFormatInjector()
        fragment = injector._get_fragment(OutputFormat.EXPLAIN)
        assert injector._estimate_tokens(fragment) <= MAX_FRAGMENT_TOKENS

    def test_get_fragment_cached(self):
        """Test that fragments are cached."""
        injector = ResponseFormatInjector()
        frag1 = injector._get_fragment(OutputFormat.GENERAL)
        frag2 = injector._get_fragment(OutputFormat.GENERAL)
        assert frag1 is frag2

    def test_inject_none_system_prompt(self):
        """Test injection with no system prompt."""
        injector = ResponseFormatInjector()
        result = injector.inject(None, OutputFormat.GENERAL)
        assert result is not None
        assert len(result) > 0

    def test_inject_empty_system_prompt(self):
        """Test injection with empty system prompt."""
        injector = ResponseFormatInjector()
        result = injector.inject("", OutputFormat.CODE)
        assert "code" in result.lower() or "output" in result.lower()

    def test_inject_normal_system_prompt(self):
        """Test injection with normal system prompt."""
        injector = ResponseFormatInjector()
        result = injector.inject("You are a helpful assistant.", OutputFormat.GENERAL)
        assert "helpful" in result.lower()
        assert "concise" in result.lower()

    def test_inject_skips_existing_instructions(self):
        """Test that injection is skipped if instructions exist."""
        injector = ResponseFormatInjector()
        result = injector.inject("Be concise please.", OutputFormat.GENERAL)
        assert result == "Be concise please."

    def test_inject_appends_not_prepends(self):
        """Test that fragment is appended, not prepended."""
        injector = ResponseFormatInjector()
        result = injector.inject("You are helpful.", OutputFormat.GENERAL)
        assert result.startswith("You are helpful.")

    def test_inject_respects_length_limit(self):
        """Test that injection respects token limit."""
        injector = ResponseFormatInjector()
        long_prompt = " ".join(["word"] * 1100)
        result = injector.inject(long_prompt, OutputFormat.GENERAL)
        assert result == long_prompt


class TestFragmentLibrary:
    """Tests for fragment library."""

    def test_fragment_library_has_all_formats(self):
        """Test that all output formats have fragments."""
        for fmt in OutputFormat:
            assert fmt in FRAGMENT_LIBRARY

    def test_fragment_library_max_tokens(self):
        """Test that all fragments are within token limit."""
        injector = ResponseFormatInjector()
        for fmt, fragment in FRAGMENT_LIBRARY.items():
            assert injector._estimate_tokens(fragment) <= MAX_FRAGMENT_TOKENS + 2


class TestProcessMethod:
    """Tests for the process method."""

    def test_process_returns_stage_output(self):
        """Test process returns StageOutput."""
        injector = ResponseFormatInjector()
        intent = IntentSchema(core_task="test", output_format=OutputFormat.GENERAL)
        inp = StageInput(prompt="test", intent=intent, token_count=5, system_prompt="You are helpful.")

        out = injector.process(inp)
        assert isinstance(out, StageOutput)

    def test_process_unknown_format_defaults_to_general(self):
        """Test that UNKNOWN format defaults to GENERAL."""
        injector = ResponseFormatInjector()
        intent = IntentSchema(core_task="test", output_format=OutputFormat.UNKNOWN)
        inp = StageInput(prompt="test", intent=intent, token_count=5, system_prompt=None)

        out = injector.process(inp)
        assert out.metadata["output_format"] == OutputFormat.GENERAL.value

    def test_process_injects_fragment(self):
        """Test that fragment is injected."""
        injector = ResponseFormatInjector()
        intent = IntentSchema(core_task="test", output_format=OutputFormat.CODE)
        inp = StageInput(prompt="test", intent=intent, token_count=5, system_prompt="You are helpful.")

        out = injector.process(inp)
        assert out.metadata["was_injected"] is True

    def test_process_skips_existing(self):
        """Test that existing instructions are detected."""
        injector = ResponseFormatInjector()
        intent = IntentSchema(core_task="test", output_format=OutputFormat.GENERAL)
        inp = StageInput(prompt="test", intent=intent, token_count=5, system_prompt="Be concise.")

        out = injector.process(inp)
        assert out.metadata["was_injected"] is False
        assert out.metadata["skip_reason"] is not None

    def test_process_metadata(self):
        """Test that process includes proper metadata."""
        injector = ResponseFormatInjector()
        intent = IntentSchema(core_task="test", output_format=OutputFormat.LIST)
        inp = StageInput(prompt="test", intent=intent, token_count=5, system_prompt="You are an assistant.")

        out = injector.process(inp)
        assert "original_system_prompt" in out.metadata
        assert "modified_system_prompt" in out.metadata
        assert "output_format" in out.metadata
        assert "fragment_used" in out.metadata
        assert "was_injected" in out.metadata


class TestConstants:
    """Tests for constant values."""

    def test_max_fragment_tokens_is_positive(self):
        """Test max fragment tokens is positive."""
        assert MAX_FRAGMENT_TOKENS > 0

    def test_max_fragment_tokens_reasonable(self):
        """Test max fragment tokens is reasonable."""
        assert MAX_FRAGMENT_TOKENS <= 20


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_prompt_injection(self):
        """Test injection with empty prompt."""
        injector = ResponseFormatInjector()
        result = injector.inject("", OutputFormat.GENERAL)
        assert len(result) > 0

    def test_special_characters(self):
        """Test handling of special characters."""
        injector = ResponseFormatInjector()
        result = injector.inject("You are @helpful# assistant!", OutputFormat.GENERAL)
        assert "@helpful" in result or "concise" in result.lower()

    def test_unicode_content(self):
        """Test handling of unicode content."""
        injector = ResponseFormatInjector()
        result = injector.inject("You are émojis 🎉", OutputFormat.GENERAL)
        assert "🎉" in result or "concise" in result.lower()
