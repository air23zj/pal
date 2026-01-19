"""
Embedding Generation Service

Provides unified interface for generating text embeddings using multiple backends:
- OpenAI embeddings (production)
- Sentence transformers (local/dev)
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batched for efficiency)"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension size"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embeddings (ada-002)"""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-ada-002"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._dimension = 1536  # ada-002 dimension

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        response = self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        # OpenAI supports batch requests (up to 2048 texts at once)
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    def get_dimension(self) -> int:
        return self._dimension


class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence transformers (all-MiniLM-L6-v2)"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize sentence transformer model

        Args:
            model_name: HuggingFace model name
                - all-MiniLM-L6-v2: Fast, 384 dim (default)
                - all-mpnet-base-v2: Better quality, 768 dim
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        return self._dimension


class EmbeddingService:
    """
    Unified embedding service with automatic provider selection

    Tries providers in order:
    1. OpenAI (if OPENAI_API_KEY set)
    2. SentenceTransformers (local fallback)
    """

    def __init__(self, provider: Optional[EmbeddingProvider] = None):
        """
        Initialize embedding service

        Args:
            provider: Optional explicit provider. If None, auto-detect.
        """
        if provider:
            self.provider = provider
        else:
            self.provider = self._auto_detect_provider()

    def _auto_detect_provider(self) -> EmbeddingProvider:
        """Auto-detect and initialize best available provider"""

        # Try OpenAI first (production)
        if os.getenv("OPENAI_API_KEY"):
            try:
                return OpenAIEmbeddingProvider()
            except (ImportError, ValueError):
                pass

        # Fallback to sentence transformers (local)
        try:
            return SentenceTransformerProvider()
        except ImportError:
            raise RuntimeError(
                "No embedding provider available. Install openai or sentence-transformers."
            )

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.get_dimension()

        return self.provider.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched)

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts but preserve indices
        filtered_texts = []
        empty_indices = []

        for i, text in enumerate(texts):
            if text and text.strip():
                filtered_texts.append(text)
            else:
                empty_indices.append(i)

        # Get embeddings for non-empty texts
        embeddings = self.provider.embed_batch(filtered_texts) if filtered_texts else []

        # Insert zero vectors for empty texts
        zero_vector = [0.0] * self.get_dimension()
        for idx in empty_indices:
            embeddings.insert(idx, zero_vector)

        return embeddings

    def get_dimension(self) -> int:
        """Get embedding vector dimension"""
        return self.provider.get_dimension()

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Similarity score 0.0-1.0 (1.0 = identical)
        """
        # Convert to numpy for efficient computation
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Compute cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Singleton instance for easy import
_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create singleton embedding service"""
    global _service_instance
    if _service_instance is None:
        _service_instance = EmbeddingService()
    return _service_instance
