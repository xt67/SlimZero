"""
SlimZero Semantic Guard Stage (Stage 3)

Primary safety mechanism that ensures rewritten prompts preserve meaning.
Computes cosine similarity between original and rewritten prompts.
Non-bypassable - cannot be disabled, only threshold adjusted.
"""

from typing import Optional, Tuple
import logging

from slimzero.schemas import StageInput, StageOutput
from slimzero.exceptions import SlimZeroSemanticRejection

logger = logging.getLogger(__name__)

MIN_THRESHOLD = 0.80
DEFAULT_THRESHOLD = 0.92

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    logger.warning("sentence-transformers not available. Semantic Guard will use fallback.")


class SemanticGuard:
    """
    Validates that rewritten prompts preserve semantic meaning.

    Uses sentence-transformers (all-MiniLM-L6-v2) to compute cosine similarity.
    This stage cannot be disabled - it is the one inviolable safety rule in SlimZero.
    """

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize SemanticGuard.

        Args:
            threshold: Minimum similarity threshold (0.80-1.0). Default 0.92.
            model_name: SentenceTransformer model name.

        Raises:
            ValueError: If threshold is outside valid range.
        """
        if not MIN_THRESHOLD <= threshold <= 1.0:
            raise ValueError(
                f"Threshold must be between {MIN_THRESHOLD} and 1.0, got {threshold}"
            )

        self.threshold = threshold
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

        if ST_AVAILABLE:
            try:
                self._model = SentenceTransformer(model_name)
                logger.info(f"Loaded SentenceTransformer model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load model '{model_name}': {e}")
                self._model = None

    def _is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        return ST_AVAILABLE and self._model is not None

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text1: First text (original).
            text2: Second text (rewritten).

        Returns:
            Cosine similarity score (0.0-1.0).
        """
        if not self._is_available():
            return self._fallback_similarity(text1, text2)

        try:
            if self._model is None:
                return self._fallback_similarity(text1, text2)
            embeddings = self._model.encode([text1, text2])
            emb1, emb2 = embeddings[0], embeddings[1]

            dot_product = float(sum(a * b for a, b in zip(emb1, emb2)))
            norm1 = float(sum(a * a for a in emb1) ** 0.5)
            norm2 = float(sum(a * a for a in emb2) ** 0.5)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.warning(f"Embedding computation failed: {e}")
            return self._fallback_similarity(text1, text2)

    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """
        Fallback similarity when sentence-transformers unavailable.
        Uses simple word overlap as a rough approximation.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def validate(self, original: str, rewritten: str) -> Tuple[bool, float]:
        """
        Validate that rewritten prompt is semantically similar to original.

        Args:
            original: Original prompt text.
            rewritten: Rewritten/compressed prompt text.

        Returns:
            Tuple of (is_valid, similarity_score).
            is_valid is True if similarity >= threshold.
        """
        if original == rewritten:
            return True, 1.0

        similarity = self.compute_similarity(original, rewritten)
        is_valid = similarity >= self.threshold

        if not is_valid:
            logger.info(
                f"SemanticGuard rejected rewrite: similarity={similarity:.3f}, "
                f"threshold={self.threshold:.3f}"
            )

        return is_valid, similarity

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to validate prompt against metadata.

        Args:
            inp: StageInput containing prompt and metadata.

        Returns:
            StageOutput with prompt unchanged and validation metadata.
        """
        original_prompt = inp.metadata.get("original_prompt", inp.prompt)
        rewritten_prompt = inp.metadata.get("rewritten_prompt", inp.prompt)

        is_valid, similarity = self.validate(original_prompt, rewritten_prompt)

        metadata = {
            "original_prompt": original_prompt,
            "rewritten_prompt": rewritten_prompt,
            "similarity": similarity,
            "threshold": self.threshold,
            "is_valid": is_valid,
            "st_available": self._is_available(),
        }

        if not is_valid:
            metadata["rejection_reason"] = "similarity_below_threshold"

        return StageOutput(
            prompt=rewritten_prompt if is_valid else original_prompt,
            modified=is_valid and rewritten_prompt != original_prompt,
            notes=f"Semantic similarity: {similarity:.3f} (threshold: {self.threshold:.3f})",
            metadata=metadata,
        )

    def validate_or_raise(self, original: str, rewritten: str) -> str:
        """
        Validate rewrite and raise exception if invalid.

        Args:
            original: Original prompt.
            rewritten: Rewritten prompt.

        Returns:
            The valid rewritten prompt.

        Raises:
            SlimZeroSemanticRejection: If similarity < threshold.
        """
        is_valid, similarity = self.validate(original, rewritten)

        if not is_valid:
            raise SlimZeroSemanticRejection(
                f"Rewrite rejected: similarity {similarity:.3f} below threshold {self.threshold:.3f}",
                similarity=similarity,
                threshold=self.threshold,
                context={"original": original, "rewritten": rewritten},
            )

        return rewritten
