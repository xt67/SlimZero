"""
SlimZero Shared Embedding Model

Singleton model for sentence-transformers to avoid loading multiple instances.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    SentenceTransformer = None
    logger.warning("sentence-transformers not available.")


class SharedEmbeddingModel:
    """
    Singleton wrapper for sentence-transformers SentenceTransformer.
    
    Avoids loading multiple instances of the same model (~80MB each).
    """
    
    _instance: Optional["SharedEmbeddingModel"] = None
    _model: Optional[SentenceTransformer] = None
    _model_name: str = "all-MiniLM-L6-v2"
    
    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        if cls._instance is None or model_name != cls._model_name:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if self._initialized and model_name == self._model_name:
            return
        
        self._model_name = model_name
        self._model = None
        
        if ST_AVAILABLE:
            try:
                self._model = SentenceTransformer(model_name)
                logger.info(f"Loaded shared embedding model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                self._model = None
        
        self._initialized = True
    
    @property
    def model(self) -> Optional[SentenceTransformer]:
        """Get the underlying model."""
        return self._model
    
    @property
    def is_available(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
    
    def encode(self, texts):
        """Encode texts using the shared model."""
        if self._model is None:
            raise RuntimeError("Embedding model not loaded")
        return self._model.encode(texts)
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score (0.0-1.0)
        """
        if self._model is None:
            return self._fallback_similarity(text1, text2)
        
        try:
            embeddings = self._model.encode([text1, text2])
            emb1, emb2 = embeddings[0], embeddings[1]
            
            dot = float(sum(a * b for a, b in zip(emb1, emb2)))
            norm1 = float(sum(a * a for a in emb1) ** 0.5)
            norm2 = float(sum(a * a for a in emb2) ** 0.5)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot / (norm1 * norm2)
        except Exception as e:
            logger.warning(f"Embedding similarity failed: {e}")
            return self._fallback_similarity(text1, text2)
    
    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Fallback Jaccard similarity when model unavailable."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SharedEmbeddingModel:
    """
    Get the shared embedding model instance.
    
    Args:
        model_name: Name of the model to load.
        
    Returns:
        SharedEmbeddingModel instance.
    """
    return SharedEmbeddingModel(model_name)
