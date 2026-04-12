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
from slimzero.utils import get_embedding_model

logger = logging.getLogger(__name__)

MIN_THRESHOLD = 0.80
DEFAULT_THRESHOLD = 0.92


class SemanticGuard:
    """
    Validates that rewritten prompts preserve semantic meaning.

    Uses shared sentence-transformers model (all-MiniLM-L6-v2) to compute cosine similarity.
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
        self._embedding_model = get_embedding_model(model_name)

    def _is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        return self._embedding_model.is_available

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text1: First text (original).
            text2: Second text (rewritten).

        Returns:
            Cosine similarity score (0.0-1.0).
        """
        return self._embedding_model.similarity(text1, text2)

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
