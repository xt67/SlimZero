"""
SlimZero Response Format Injector Stage (Stage 6)

Preconditions the LLM to respond minimally without preamble or padding.
Appends instruction fragments to system prompt based on detected output format.
"""

import logging
import re
from typing import Optional

from slimzero.schemas import StageInput, StageOutput, OutputFormat

logger = logging.getLogger(__name__)

FRAGMENT_LIBRARY = {
    OutputFormat.GENERAL: "Respond concisely. No preamble.",
    OutputFormat.CODE: "Output only code. No explanations.",
    OutputFormat.LIST: "Respond with a list only. No introduction.",
    OutputFormat.EXPLAIN: "Explain briefly. No padding.",
    OutputFormat.TABLE: "Output table only. No surrounding text.",
    OutputFormat.UNKNOWN: "Be concise.",
}

MAX_FRAGMENT_TOKENS = 12
RESPONSE_INSTRUCTION_PATTERNS = [
    r"\bconcise(ly)?\b",
    r"\bbrief(ly)?\b",
    r"\bno\s+(?:intro|preamble|explanation|explain)\b",
    r"\bonly\s+(?:output|respond|provide)\b",
    r"\blist\s+only\b",
    r"\bcode\s+only\b",
]


class ResponseFormatInjector:
    """
    Injects response format instructions into system prompts.

    Appends instruction fragments to encourage minimal responses.
    Never prepends to avoid displacing developer's system prompt.
    """

    def __init__(self):
        """Initialize ResponseFormatInjector."""
        self._fragment_cache: dict[OutputFormat, str] = {}

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text.split())

    def _has_response_instructions(self, text: str) -> bool:
        """Check if text already contains response-length instructions."""
        if not text:
            return False

        text_lower = text.lower()
        for pattern in RESPONSE_INSTRUCTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        return False

    def _get_fragment(self, output_format: OutputFormat) -> str:
        """Get instruction fragment for output format."""
        if output_format in self._fragment_cache:
            return self._fragment_cache[output_format]

        fragment = FRAGMENT_LIBRARY.get(output_format, FRAGMENT_LIBRARY[OutputFormat.UNKNOWN])
        tokens = self._estimate_tokens(fragment)

        if tokens > MAX_FRAGMENT_TOKENS:
            words = fragment.split()
            truncated = " ".join(words[:MAX_FRAGMENT_TOKENS])
            if truncated.endswith((".", "!", "?")):
                fragment = truncated
            else:
                last_punct = max(
                    truncated.rfind(p) for p in (".", "!", "?")
                )
                if last_punct > 0:
                    fragment = truncated[:last_punct + 1]
                else:
                    fragment = truncated

        self._fragment_cache[output_format] = fragment
        return fragment

    def inject(
        self,
        system_prompt: Optional[str],
        output_format: OutputFormat,
    ) -> str:
        """
        Inject response format instructions into system prompt.

        Args:
            system_prompt: The system prompt to modify (can be None).
            output_format: Detected output format from Intent Extractor.

        Returns:
            System prompt with response format instructions appended.
        """
        fragment = self._get_fragment(output_format)

        if not system_prompt:
            return fragment

        if self._has_response_instructions(system_prompt):
            logger.info("System prompt already contains response instructions, skipping injection")
            return system_prompt

        current_tokens = self._estimate_tokens(system_prompt)
        if current_tokens + self._estimate_tokens(fragment) > 1000:
            logger.warning("System prompt too long, skipping injection")
            return system_prompt

        return f"{system_prompt}\n\n{fragment}"

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to inject response format instructions.

        Args:
            inp: StageInput containing intent and system prompt.

        Returns:
            StageOutput with modified system prompt and metadata.
        """
        system_prompt = inp.system_prompt
        output_format = inp.intent.output_format

        if output_format == OutputFormat.UNKNOWN:
            output_format = OutputFormat.GENERAL

        original_prompt = system_prompt or ""
        modified_prompt = self.inject(system_prompt, output_format)
        was_injected = modified_prompt != original_prompt

        return StageOutput(
            prompt=inp.prompt,
            modified=was_injected,
            notes=f"Response format: {output_format.value}" + (" (injected)" if was_injected else " (skipped)"),
            metadata={
                "original_system_prompt": original_prompt,
                "modified_system_prompt": modified_prompt,
                "output_format": output_format.value,
                "fragment_used": self._get_fragment(output_format),
                "was_injected": was_injected,
                "skip_reason": None if was_injected else (
                    "already_has_instructions" if self._has_response_instructions(original_prompt) else "prompt_too_long"
                    if original_prompt and self._estimate_tokens(original_prompt) > 900 else None
                ),
            },
        )
