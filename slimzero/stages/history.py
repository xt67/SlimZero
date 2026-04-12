"""
SlimZero History Compressor Stage (Stage 5)

Compresses conversation history to manage context window efficiently.
Keeps recent turns verbatim, summarizes older turns.
"""

import logging
from typing import Optional, List, Dict, Tuple

from slimzero.schemas import StageInput, StageOutput

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. History Compressor will use truncation fallback.")

DEFAULT_WINDOW = 4
MIN_WINDOW = 2
SUMMARY_BUDGET_RATIO = 0.20


class HistoryCompressor:
    """
    Compresses conversation history to manage context window.

    Keeps last N turns verbatim, summarizes older turns into 'Prior context:' block.
    Caches summaries and regenerates only when turn count threshold crossed.
    """

    def __init__(
        self,
        window: int = DEFAULT_WINDOW,
        summary_budget_ratio: float = SUMMARY_BUDGET_RATIO,
        model_name: str = "t5-small",
    ):
        """
        Initialize HistoryCompressor.

        Args:
            window: Number of recent turns to keep verbatim. Default 4.
            summary_budget_ratio: Max ratio of summary tokens to total budget. Default 0.20.
            model_name: T5 model for summarization.
        """
        self.window = max(MIN_WINDOW, min(window, 10))
        self.summary_budget_ratio = max(0.05, min(0.5, summary_budget_ratio))
        self.model_name = model_name
        self._summarizer = None
        self._tokenizer = None
        self._cache: Dict[str, Tuple[str, int]] = {}
        self._last_turn_count = 0

        if TRANSFORMERS_AVAILABLE:
            self._init_summarizer()

    def _init_summarizer(self) -> None:
        """Initialize T5 summarization pipeline."""
        try:
            self._summarizer = pipeline(
                "summarization",
                model=self.model_name,
                tokenizer=self.model_name,
            )
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info(f"Loaded T5 summarizer: {self.model_name}")
        except Exception as e:
            logger.warning(f"T5 summarizer init failed: {e}")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using word approximation."""
        return len(text.split())

    def _get_cache_key(self, history: List[Dict[str, str]]) -> str:
        """Generate cache key from history."""
        if not history:
            return ""
        turns = [f"{h.get('role', '')}:{h.get('content', '')[:50]}" for h in history]
        return "|".join(turns[-self.window:])

    def _summarize_turns(self, turns: List[Dict[str, str]], budget: int) -> str:
        """Summarize older turns into a context block."""
        if not turns or not self._summarizer:
            return ""

        combined = " ".join(
            f"{t.get('role', 'user')}: {t.get('content', '')}" for t in turns
        )

        max_summary_tokens = int(budget * self.summary_budget_ratio)
        max_new_tokens = min(max_summary_tokens, 100)

        try:
            summary = self._summarizer(
                combined[:1000],
                max_new_tokens=max_new_tokens,
                min_length=10,
                do_sample=False,
            )
            if summary and summary[0].get("summary_text"):
                result = summary[0]["summary_text"].strip()
                if self._estimate_tokens(result) <= max_summary_tokens:
                    return result
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")

        return self._truncate_turns(turns, budget)

    def _truncate_turns(self, turns: List[Dict[str, str]], budget: int) -> str:
        """Fallback: truncate turns to fit budget."""
        result_parts = []
        remaining_budget = int(budget * self.summary_budget_ratio)

        for turn in turns:
            content = turn.get("content", "")
            turn_text = f"{turn.get('role', 'user')}: {content}"
            turn_tokens = self._estimate_tokens(turn_text)

            if turn_tokens <= remaining_budget:
                result_parts.append(turn_text)
                remaining_budget -= turn_tokens
            else:
                break

        return " ".join(result_parts[-3:]) if result_parts else ""

    def compress(
        self,
        history: Optional[List[Dict[str, str]]],
        token_budget: int = 512,
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Compress conversation history.

        Args:
            history: List of conversation turns with 'role' and 'content' keys.
            token_budget: Total token budget for the prompt.

        Returns:
            Tuple of (compressed_history, prior_context_summary).
            prior_context_summary is None if all turns fit in window.
        """
        if not history:
            return [], None

        history = list(history)
        self._last_turn_count = len(history)

        if len(history) <= self.window:
            return history, None

        cache_key = self._get_cache_key(history)
        if cache_key in self._cache:
            cached_summary, cached_turns = self._cache[cache_key]
            if cached_turns == len(history):
                return history[-self.window:], cached_summary

        recent_turns = history[-self.window:]
        older_turns = history[:-self.window]

        prior_context = self._summarize_turns(older_turns, token_budget)

        if prior_context:
            self._cache[cache_key] = (prior_context, len(history))

        return recent_turns, prior_context if prior_context else None

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to compress history.

        Args:
            inp: StageInput containing history.

        Returns:
            StageOutput with compressed history and summary.
        """
        history = inp.history or []
        budget = inp.token_count

        compressed_history, prior_context = self.compress(history, budget)

        history_modified = len(compressed_history) < len(history)
        notes_parts = []

        if history_modified:
            notes_parts.append(f"Kept {len(compressed_history)} recent turns")
        else:
            notes_parts.append(f"All {len(history)} turns retained verbatim")

        if prior_context:
            notes_parts.append(f"Prior context: {self._estimate_tokens(prior_context)} tokens")

        return StageOutput(
            prompt=inp.prompt,
            modified=history_modified or prior_context is not None,
            notes="; ".join(notes_parts),
            metadata={
                "original_turns": len(history),
                "compressed_turns": len(compressed_history),
                "prior_context": prior_context,
                "prior_context_tokens": self._estimate_tokens(prior_context) if prior_context else 0,
                "window": self.window,
                "summary_budget_ratio": self.summary_budget_ratio,
                "cache_size": len(self._cache),
            },
        )
