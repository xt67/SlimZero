"""
SlimZero Token Budget Enforcer Stage (Stage 8)

Enforces a hard token ceiling on prompts with priority-based trimming.
Uses tiktoken for accurate token counting.
"""

import logging
from typing import Optional, List, Tuple, Dict, Any

from slimzero.schemas import StageInput, StageOutput

logger = logging.getLogger(__name__)

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available. Token Budget Enforcer will use word-based estimation.")

TRIM_PRIORITY = [
    "injected_fragments",
    "history_summary",
    "low_ranked_examples",
    "compressed_rewrite",
]

MIN_CORE_TASK_TOKENS = 5
DEFAULT_BUDGET = 4096


class TokenBudgetEnforcer:
    """
    Enforces hard token ceiling on prompts with priority-based trimming.

    Trim order (first to last):
    1. Injected fragments
    2. Old history summary
    3. Low-ranked examples beyond top-1
    4. Compressed rewrite
    """

    def __init__(
        self,
        token_budget: int = DEFAULT_BUDGET,
        encodings: Optional[List[str]] = None,
    ):
        """
        Initialize TokenBudgetEnforcer.

        Args:
            token_budget: Maximum tokens allowed. Default 512.
            encodings: List of encoding names to try (cl100k_base, o200k_base, etc.)
        """
        self.token_budget = max(50, min(token_budget, 100000))
        self.encodings = encodings or ["cl100k_base", "o200k_base", "p50k_base"]
        self._encoder: tiktoken.Encoding = None
        self._encoding_name: Optional[str] = None

        if TIKTOKEN_AVAILABLE:
            self._init_encoder()

    def _init_encoder(self) -> None:
        """Initialize tiktoken encoder with fallback."""
        for encoding_name in self.encodings:
            try:
                self._encoder = tiktoken.get_encoding(encoding_name)
                self._encoding_name = encoding_name
                logger.info(f"Loaded tiktoken encoding: {encoding_name}")
                return
            except Exception:
                continue

        logger.warning("Failed to load tiktoken encodings, using word-based estimation")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using word approximation."""
        if not text:
            return 0
        return len(text.split())

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for.

        Returns:
            Token count.
        """
        if not text:
            return 0

        if self._encoder:
            try:
                return len(self._encoder.encode(text))
            except Exception as e:
                logger.warning(f"Encoding failed: {e}")

        return self._estimate_tokens(text)

    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> int:
        """
        Count tokens for a message array.

        Args:
            messages: List of messages with 'role' and 'content'.
            system_prompt: Optional system prompt.

        Returns:
            Total token count.
        """
        total = 0

        if system_prompt:
            total += self.count_tokens(system_prompt) + 3

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            total += self.count_tokens(content) + 4

        total += 3
        return total

    def _trim_components(
        self,
        components: Dict[str, str],
        current_tokens: int,
    ) -> Tuple[Dict[str, str], int, List[str]]:
        """
        Trim components to fit budget.

        Args:
            components: Dict of component_name -> content.
            current_tokens: Current token count.

        Returns:
            Tuple of (trimmed_components, final_token_count, trimmed_items).
        """
        if current_tokens <= self.token_budget:
            return components, current_tokens, []

        trimmed = dict(components)
        trimmed_items: List[str] = []

        for priority_key in TRIM_PRIORITY:
            if priority_key not in trimmed:
                continue

            while current_tokens > self.token_budget:
                content = trimmed[priority_key]
                if not content or len(content) < 10:
                    break

                words = content.split()
                if len(words) <= 2:
                    del trimmed[priority_key]
                    trimmed_items.append(priority_key)
                    break

                new_content = " ".join(words[:-2])
                trimmed[priority_key] = new_content
                current_tokens = self.count_tokens(" ".join(trimmed.values()))

                if current_tokens <= self.token_budget:
                    break

        return trimmed, current_tokens, trimmed_items

    def enforce(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        few_shot_examples: Optional[List[str]] = None,
        injected_fragment: Optional[str] = None,
        prior_context: Optional[str] = None,
    ) -> Tuple[str, Optional[str], List[str]]:
        """
        Enforce token budget on prompt components.

        Args:
            prompt: Core prompt text.
            system_prompt: System prompt.
            history: Conversation history.
            few_shot_examples: Few-shot examples.
            injected_fragment: Response format fragment.
            prior_context: Summarized prior context.

        Returns:
            Tuple of (final_prompt, modified_system_prompt, trimmed_items).
        """
        if not prompt:
            return "", system_prompt, []

        components: Dict[str, str] = {"prompt": prompt}
        trimmed_items: List[str] = []

        if system_prompt:
            components["system"] = system_prompt
        if injected_fragment:
            components["fragment"] = injected_fragment
        if prior_context:
            components["prior_context"] = prior_context
        if history:
            history_text = " ".join(
                f"{h.get('role', '')}: {h.get('content', '')}" for h in history[-4:]
            )
            components["history"] = history_text
        if few_shot_examples:
            components["examples"] = "\n".join(few_shot_examples[:2])

        current_tokens = self.count_tokens(" ".join(components.values()))

        if current_tokens <= self.token_budget:
            return prompt, system_prompt, []

        components, final_tokens, trimmed_items = self._trim_components(
            components, current_tokens
        )

        final_parts = []
        if components.get("fragment"):
            final_parts.append(components["fragment"])
        if components.get("system"):
            final_parts.append(components["system"])
        if components.get("prior_context"):
            final_parts.append(f"Prior context: {components['prior_context']}")
        if components.get("history"):
            final_parts.append(components["history"])
        if components.get("examples"):
            final_parts.append(components["examples"])
        final_parts.append(components.get("prompt", prompt))

        final_prompt = "\n\n".join(final_parts)
        modified_system = components.get("system")

        return final_prompt, modified_system, trimmed_items

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to enforce token budget.

        Args:
            inp: StageInput containing prompt and components.

        Returns:
            StageOutput with budget-enforced prompt.
        """
        original_tokens = self.count_tokens(inp.prompt)
        prior_context = inp.metadata.get("prior_context")
        injected_fragment = inp.metadata.get("injected_fragment")
        few_shot_examples = inp.few_shot_examples

        final_prompt, modified_system, trimmed_items = self.enforce(
            prompt=inp.prompt,
            system_prompt=inp.system_prompt,
            history=inp.history,
            few_shot_examples=few_shot_examples,
            injected_fragment=injected_fragment,
            prior_context=prior_context,
        )

        final_tokens = self.count_tokens(final_prompt)
        was_trimmed = len(trimmed_items) > 0

        return StageOutput(
            prompt=final_prompt,
            modified=was_trimmed or final_tokens < original_tokens,
            notes=f"Budget: {final_tokens}/{self.token_budget} tokens" + (
                f" (trimmed: {', '.join(trimmed_items)})" if trimmed_items else ""
            ),
            token_count=final_tokens,
            metadata={
                "original_tokens": original_tokens,
                "final_tokens": final_tokens,
                "token_budget": self.token_budget,
                "within_budget": final_tokens <= self.token_budget,
                "trimmed_items": trimmed_items,
                "encoding_used": self._encoding_name,
                "tiktoken_available": TIKTOKEN_AVAILABLE,
            },
        )
