"""
SlimZero Few-Shot Ranker Stage (Stage 4)

Retains only the most relevant few-shot examples to reduce token overhead.
Uses sentence-transformers for semantic similarity ranking.
"""

import re
import logging
from typing import Optional, List, Tuple

from slimzero.schemas import StageInput, StageOutput
from slimzero.utils import get_embedding_model

logger = logging.getLogger(__name__)

DEFAULT_K = 3
MIN_K = 1

Q_A_PATTERN = re.compile(r"(?:^|\n)(Q:?\s*(.+?)[\n\r]+A:?\s*(.+?))(?=\n\n|\n(?:Q:)|$)", re.IGNORECASE | re.MULTILINE | re.DOTALL)
NUMBERED_PATTERN = re.compile(r"^\s*(?:\d+[.)]\s*)?(.+?)(?:\n|$)", re.MULTILINE)
XML_TAG_PATTERN = re.compile(r"<(?:\w+)>(.+?)</(?:\w+)>", re.DOTALL)

ANSWER_SEPARATORS = ["\nA:", "\nAnswer:", "\nA.", "\n"]


class FewShotRanker:
    """
    Ranks and filters few-shot examples by relevance to the current query.

    Uses shared sentence-transformers model for cosine similarity.
    Falls back to keyword matching if transformers unavailable.
    """

    def __init__(
        self,
        k: int = DEFAULT_K,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize FewShotRanker.

        Args:
            k: Number of top examples to retain. Default 3.
            model_name: SentenceTransformer model for embeddings.
        """
        self.k = max(MIN_K, min(k, 10))
        self.model_name = model_name
        self._embedding_model = get_embedding_model(model_name)

    def _is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        return self._embedding_model.is_available

    def _detect_examples(self, text: str) -> List[str]:
        """Detect few-shot examples using pattern matching."""
        examples: List[str] = []

        qa_blocks = re.split(r"(?=\n\s*\n\s*Q:)", text)
        for block in qa_blocks:
            block = block.strip()
            if not block or "A:" not in block.upper():
                continue
            parts = re.split(r"\n\s*A:\s*", block, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) < 2:
                continue
            q_text = parts[0].strip()
            a_text = parts[1].strip()
            if q_text and a_text and q_text.startswith("Q"):
                example = f"Q: {q_text[1:].strip()}\nA: {a_text}"
                if example not in examples:
                    examples.append(example)

        if len(examples) < 2:
            xml_matches = XML_TAG_PATTERN.findall(text)
            for i in range(0, len(xml_matches) - 1, 2):
                if i + 1 < len(xml_matches):
                    example = f"{xml_matches[i].strip()}\n{xml_matches[i + 1].strip()}"
                    if example not in examples and len(example) > 10:
                        examples.append(example)

        if len(examples) < 2:
            parts = re.split(r"\n\n+", text)
            for part in parts:
                part = part.strip()
                if part and len(part.split()) >= 4:
                    for sep in ANSWER_SEPARATORS:
                        if sep in part.lower():
                            if part not in examples:
                                examples.append(part)
                            break

        return examples

    def _keyword_score(self, example: str, query: str) -> float:
        """Compute keyword-based relevance score."""
        example_words = set(w.lower() for w in re.findall(r"\w+", example))
        query_words = set(w.lower() for w in re.findall(r"\w+", query))

        if not query_words:
            return 0.0

        overlap = len(example_words & query_words)
        return overlap / len(query_words)

    def _rank_with_embeddings(self, examples: List[str], query: str) -> List[Tuple[str, float]]:
        """Rank examples using shared sentence embeddings model."""
        if not examples:
            return []

        try:
            ranked: List[Tuple[str, float]] = []
            for ex in examples:
                score = self._embedding_model.similarity(query, ex)
                ranked.append((ex, score))

            ranked.sort(key=lambda x: x[1], reverse=True)
            return ranked
        except Exception as e:
            logger.warning(f"Embedding ranking failed: {e}")
            return [(ex, self._keyword_score(ex, query)) for ex in examples]

    def _rank_with_keywords(self, examples: List[str], query: str) -> List[Tuple[str, float]]:
        """Rank examples using keyword overlap."""
        scored = [(ex, self._keyword_score(ex, query)) for ex in examples]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def rank(self, text: str, query: str) -> List[str]:
        """
        Rank and filter few-shot examples by relevance.

        Args:
            text: Text containing few-shot examples.
            query: Current user query.

        Returns:
            List of top-k examples (or at least 1 if any exist).
        """
        if not text or not query:
            return []

        examples = self._detect_examples(text)

        if len(examples) < 2:
            return examples if examples else []

        if self._is_available():
            ranked = self._rank_with_embeddings(examples, query)
        else:
            ranked = self._rank_with_keywords(examples, query)

        top_k = min(self.k, len(ranked))
        if top_k < 1 and len(examples) >= 1:
            top_k = 1

        return [ex for ex, _ in ranked[:top_k]]

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to rank few-shot examples.

        Args:
            inp: StageInput containing prompt and few-shot examples.

        Returns:
            StageOutput with ranked examples.
        """
        examples = inp.few_shot_examples or []
        query = inp.prompt

        if not examples:
            return StageOutput(
                prompt=inp.prompt,
                modified=False,
                notes="No few-shot examples to rank",
                metadata={
                    "few_shot_mode": "keyword" if not self._is_available() else "embedding",
                    "examples_count": 0,
                    "retained_count": 0,
                    "k": self.k,
                },
            )

        if len(examples) < 2:
            return StageOutput(
                prompt=inp.prompt,
                modified=False,
                notes=f"Few-shot: {len(examples)} example(s) (below minimum of 2, keeping all)",
                metadata={
                    "few_shot_mode": "keyword" if not self._is_available() else "embedding",
                    "examples_count": len(examples),
                    "retained_count": len(examples),
                    "k": self.k,
                },
            )

        ranked = self.rank("\n\n".join(examples), query)
        retained_count = len(ranked)

        return StageOutput(
            prompt=inp.prompt,
            modified=retained_count < len(examples),
            notes=f"Few-shot: {retained_count}/{len(examples)} examples retained (k={self.k})",
            metadata={
                "few_shot_mode": "keyword" if not self._is_available() else "embedding",
                "examples_count": len(examples),
                "retained_count": retained_count,
                "retained_examples": ranked,
                "k": self.k,
                "st_available": self._is_available(),
            },
        )
