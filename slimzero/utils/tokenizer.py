"""
SlimZero Tokenizer Utility

Shared token counting using tiktoken with word-based fallback.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available. Using word-based fallback for token counting.")


class TokenCounter:
    """
    Shared token counter for SlimZero.

    Uses tiktoken for accurate counting with word-based fallback.
    """

    _instances: dict = {}

    def __new__(cls, model: str = "cl100k_base"):
        if model not in cls._instances:
            cls._instances[model] = super().__new__(cls)
            cls._instances[model]._initialized = False
        return cls._instances[model]

    def __init__(self, model: str = "cl100k_base"):
        if self._initialized:
            return
        self.model = model
        self._encoder = None
        self._init_encoder()
        self._initialized = True

    def _init_encoder(self) -> None:
        if not TIKTOKEN_AVAILABLE:
            logger.info("Using word-based fallback for token counting")
            return

        try:
            self._encoder = tiktoken.get_encoding(self.model)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoding '{self.model}': {e}")
            self._encoder = None

    def count(self, text: str) -> int:
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
            return len(self._encoder.encode(text))

        return len(text.split())

    def count_messages(self, messages: list[dict]) -> int:
        """
        Count tokens in a messages array.

        Args:
            messages: List of message dicts with role and content.

        Returns:
            Total token count including overhead.
        """
        if not self._encoder:
            total = 0
            for msg in messages:
                total += len(msg.get("content", "").split())
                total += 4
            return total

        total = 0
        for msg in messages:
            total += 4
            for key, value in msg.items():
                total += len(self._encoder.encode(str(value)))
                if key == "name":
                    total -= 1
        total += 2
        return total


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count.
        model: Encoding model (cl100k_base for GPT-4, o200k_base for Claude).

    Returns:
        Token count.
    """
    counter = TokenCounter(model)
    return counter.count(text)
