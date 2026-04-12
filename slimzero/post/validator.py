"""
SlimZero Response Validator (post-processing)

Validates that LLM responses address the parsed intent.
Uses cosine similarity between intent core task and response.
"""

import logging
from typing import Optional, Tuple

from slimzero.schemas import IntentSchema, HallucinationRiskTier

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    logger.warning("sentence-transformers not available. Response Validator will use keyword fallback.")

DEFAULT_THRESHOLD = 0.60
MAX_RESPONSE_TOKENS = 512


class ResponseValidator:
    """
    Validates that LLM responses address the parsed intent.

    Uses cosine similarity between intent core task and response embeddings.
    Response always returned to user - never suppressed.
    """

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize ResponseValidator.

        Args:
            threshold: Minimum similarity threshold. Default 0.60.
            model_name: SentenceTransformer model for embeddings.
        """
        self.threshold = max(0.0, min(1.0, threshold))
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

        if ST_AVAILABLE:
            self._init_model()

    def _init_model(self) -> None:
        """Initialize sentence transformer model."""
        try:
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded ResponseValidator model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load model '{self.model_name}': {e}")

    def _is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        return ST_AVAILABLE and self._model is not None

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        if not text:
            return 0
        return len(text.split())

    def _compute_keyword_similarity(self, intent: str, response: str) -> float:
        """Compute keyword-based similarity fallback."""
        intent_words = set(intent.lower().split())
        response_words = set(response.lower().split())

        if not intent_words or not response_words:
            return 0.0

        intersection = intent_words & response_words
        union = intent_words | response_words

        return len(intersection) / len(union) if union else 0.0

    def _compute_embedding_similarity(self, intent: str, response: str) -> float:
        """Compute embedding-based similarity."""
        if not self._model:
            return self._compute_keyword_similarity(intent, response)

        try:
            embeddings = self._model.encode([intent, response])
            emb1, emb2 = embeddings[0], embeddings[1]

            dot_product = float(sum(a * b for a, b in zip(emb1, emb2)))
            norm1 = float(sum(a * a for a in emb1) ** 0.5)
            norm2 = float(sum(a * a for a in emb2) ** 0.5)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.warning(f"Embedding computation failed: {e}")
            return self._compute_keyword_similarity(intent, response)

    def validate(
        self,
        intent: IntentSchema,
        response: str,
    ) -> Tuple[bool, float]:
        """
        Validate that response addresses intent.

        Args:
            intent: Parsed intent from IntentSchema.
            response: LLM response text.

        Returns:
            Tuple of (is_valid, similarity_score).
        """
        if not response or not response.strip():
            return False, 0.0

        if not intent.core_task:
            return True, 1.0

        truncated_response = response
        response_tokens = self._estimate_tokens(response)
        if response_tokens > MAX_RESPONSE_TOKENS:
            words = response.split()
            truncated_response = " ".join(words[:MAX_RESPONSE_TOKENS])

        if self._is_available():
            similarity = self._compute_embedding_similarity(
                intent.core_task, truncated_response
            )
        else:
            similarity = self._compute_keyword_similarity(
                intent.core_task, truncated_response
            )

        is_valid = similarity >= self.threshold

        if not is_valid:
            logger.warning(
                f"ResponseValidator: similarity {similarity:.3f} below threshold {self.threshold:.3f}"
            )

        return is_valid, similarity

    def validate_with_metadata(
        self,
        intent: IntentSchema,
        response: str,
    ) -> dict:
        """
        Validate response and return full metadata.

        Args:
            intent: Parsed intent from IntentSchema.
            response: LLM response text.

        Returns:
            Dict with validation results and metadata.
        """
        is_valid, similarity = self.validate(intent, response)

        return {
            "is_valid": is_valid,
            "similarity": similarity,
            "threshold": self.threshold,
            "response_length": len(response),
            "response_tokens": self._estimate_tokens(response),
            "intent_core_task": intent.core_task[:100] if intent.core_task else "",
            "st_available": self._is_available(),
            "validation_passed": is_valid,
        }
