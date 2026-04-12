"""
SlimZero Prompt Rewriter Stage (Stage 2)

Compresses prompts into minimal imperative form while preserving meaning.
Uses T5-small for rewriting, with Ollama fallback.
"""

import re
import logging
from typing import Optional

from slimzero.schemas import StageInput, StageOutput

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Prompt rewriting will use rule-based fallback.")

FILLER_PATTERNS = [
    r"\bplease\b",
    r"\bcould you\b",
    r"\bwould you\b",
    r"\bcan you\b",
    r"\bkindly\b",
    r"\bif you could\b",
    r"\bi was wondering\b",
    r"\bi'd like to\b",
    r"\bI would like to\b",
    r"\bI wonder if you could\b",
    r"\bwould be so kind as to\b",
    r"\bwould you mind\b",
    r"\bdo you think you could\b",
]

HEDGED_PATTERNS = [
    (r"\bmaybe\b", ""),
    (r"\bperhaps\b", ""),
    (r"\bmight be\b", "is"),
    (r"\bcould be\b", "is"),
    (r"\bmay be\b", "is"),
    (r"\bpossibly\b", ""),
    (r"\bI think\b", ""),
    (r"\bI believe\b", ""),
    (r"\bseems like\b", "is"),
    (r"\bappears to be\b", "is"),
]

COMPRESSION_RATIO = 0.85


class PromptRewriter:
    """
    Compresses prompts into minimal imperative form while preserving meaning.

    Uses T5-small for rewriting when available.
    Falls back to rule-based rewriting if transformers are unavailable.
    """

    def __init__(
        self,
        model_name: str = "t5-small",
        compression_ratio: float = COMPRESSION_RATIO,
        use_ollama_fallback: bool = True,
    ):
        """
        Initialize PromptRewriter.

        Args:
            model_name: T5 model to use. Defaults to t5-small.
            compression_ratio: Maximum ratio of rewritten to original token count (0.0-1.0).
            use_ollama_fallback: Whether to use Ollama if transformers unavailable.
        """
        self.model_name = model_name
        self.compression_ratio = max(0.5, min(1.0, compression_ratio))
        self.use_ollama_fallback = use_ollama_fallback
        self._rewriter = None
        self._tokenizer = None
        self._mode = "unavailable"

        if TRANSFORMERS_AVAILABLE:
            self._init_transformers()
        elif use_ollama_fallback:
            self._init_ollama()
        else:
            self._init_rule_based()

    def _init_transformers(self) -> None:
        """Initialize T5 pipeline for text simplification."""
        try:
            self._rewriter = pipeline(
                "text2text-generation",
                model=self.model_name,
                tokenizer=self.model_name,
            )
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._mode = "t5-small"
            logger.info(f"Loaded T5 model: {self.model_name}")
        except Exception as e:
            logger.warning(f"T5 initialization failed: {e}")
            if self.use_ollama_fallback:
                self._init_ollama()
            else:
                self._init_rule_based()

    def _init_ollama(self) -> None:
        """Initialize Ollama fallback connection."""
        try:
            import urllib.request
            import json

            url = "http://localhost:11434/api/generate"
            data = json.dumps({
                "model": "qwen3:1.7b",
                "prompt": "test",
                "stream": False,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req, timeout=2)
            self._mode = "ollama"
            logger.info("Ollama qwen3:1.7b available")
        except Exception:
            logger.info("Ollama unavailable, using rule-based rewriting")
            self._init_rule_based()

    def _init_rule_based(self) -> None:
        """Initialize rule-based rewriting (always available)."""
        self._mode = "rule-based"
        logger.info("Using rule-based prompt rewriting")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using word-based approximation."""
        return len(text.split())

    def _strip_filler(self, text: str) -> str:
        """Remove filler phrases from text."""
        result = text
        for pattern in FILLER_PATTERNS:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
        return " ".join(result.split())

    def _convert_hedged_to_imperative(self, text: str) -> str:
        """Convert hedged phrases to direct imperative form."""
        result = text
        for pattern, replacement in HEDGED_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return " ".join(result.split())

    def _merge_duplicate_sentences(self, text: str) -> str:
        """Merge or remove duplicate sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        seen = set()
        unique_sentences = []

        for sent in sentences:
            normalized = sent.lower().strip()
            normalized = re.sub(r"[^\w\s]", "", normalized)
            if normalized not in seen and len(normalized) > 5:
                seen.add(normalized)
                unique_sentences.append(sent)

        return " ".join(unique_sentences)

    def _rule_based_rewrite(self, prompt: str) -> str:
        """Apply rule-based rewriting strategies."""
        result = prompt
        result = self._strip_filler(result)
        result = self._convert_hedged_to_imperative(result)
        result = self._merge_duplicate_sentences(result)
        return result

    def _t5_rewrite(self, prompt: str, max_tokens: int) -> str:
        """Use T5-small to rewrite the prompt."""
        if not self._rewriter or not self._tokenizer:
            return self._rule_based_rewrite(prompt)

        try:
            simplified_prompt = f"simplify: {prompt}"
            max_new_tokens = max(10, int(max_tokens * self.compression_ratio))

            outputs = self._rewriter(
                simplified_prompt,
                max_new_tokens=max_new_tokens,
                num_beams=2,
                early_stopping=True,
            )

            if outputs and outputs[0].get("generated_text"):
                rewritten = outputs[0]["generated_text"].strip()
                if rewritten and len(rewritten) > 5:
                    return rewritten
        except Exception as e:
            logger.warning(f"T5 rewriting failed: {e}")

        return self._rule_based_rewrite(prompt)

    def _ollama_rewrite(self, prompt: str, max_tokens: int) -> str:
        """Use Ollama qwen3 to rewrite the prompt."""
        try:
            import urllib.request
            import json

            rewrite_prompt = (
                f"Rewrite this prompt to be concise and imperative, removing filler. "
                f"Keep meaning. Max words: {int(max_tokens * self.compression_ratio)}. "
                f"Only output the rewritten prompt:\n{prompt}"
            )

            data = json.dumps({
                "model": "qwen3:1.7b",
                "prompt": rewrite_prompt,
                "stream": False,
                "options": {"num_predict": int(max_tokens * self.compression_ratio)},
            }).encode("utf-8")

            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result: dict = json.loads(response.read().decode("utf-8"))
                rewritten: str = result.get("response", "").strip()

                if rewritten and len(rewritten) > 5:
                    return rewritten

        except Exception as e:
            logger.warning(f"Ollama rewriting failed: {e}")

        return self._rule_based_rewrite(prompt)

    def rewrite(self, prompt: str, token_budget: int = 512) -> str:
        """
        Rewrite a prompt to be more concise.

        Args:
            prompt: The original prompt to rewrite.
            token_budget: Maximum tokens for the rewritten prompt.

        Returns:
            The rewritten prompt, guaranteed <= compression_ratio of original.
        """
        if not prompt or not prompt.strip():
            return prompt

        original_tokens = self._estimate_tokens(prompt)
        max_allowed_tokens = int(original_tokens * self.compression_ratio)
        max_tokens = min(max_allowed_tokens, token_budget)

        if self._mode == "t5-small":
            rewritten = self._t5_rewrite(prompt, max_tokens)
        elif self._mode == "ollama":
            rewritten = self._ollama_rewrite(prompt, max_tokens)
        else:
            rewritten = self._rule_based_rewrite(prompt)

        rewritten_tokens = self._estimate_tokens(rewritten)
        if rewritten_tokens > max_allowed_tokens:
            words = rewritten.split()
            truncated = " ".join(words[:max_allowed_tokens])
            if truncated.endswith((".", "!", "?")):
                return truncated
            for punct in (".", "!", "?", ","):
                idx = truncated.rfind(f" {punct}")
                if idx > len(truncated) // 2:
                    return truncated[:idx]
            return truncated

        return rewritten

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to rewrite the prompt.

        Args:
            inp: StageInput containing the prompt and metadata.

        Returns:
            StageOutput with rewritten prompt.
        """
        original_prompt = inp.prompt
        rewritten_prompt = self.rewrite(original_prompt, inp.token_count)

        modified = rewritten_prompt != original_prompt
        new_token_count = self._estimate_tokens(rewritten_prompt)

        ratio = new_token_count / max(1, self._estimate_tokens(original_prompt))

        return StageOutput(
            prompt=rewritten_prompt,
            modified=modified,
            notes=f"Rewritten from {self._estimate_tokens(original_prompt)} to {new_token_count} tokens ({ratio:.0%})",
            token_count=new_token_count,
            metadata={
                "rewriting_mode": self._mode,
                "original_tokens": self._estimate_tokens(original_prompt),
                "compression_ratio": ratio,
                "compression_target": self.compression_ratio,
            },
        )
