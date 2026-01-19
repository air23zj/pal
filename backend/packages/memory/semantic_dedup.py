"""
Semantic Deduplication Service

Detects semantically similar items even when wording differs:
- Uses vector embeddings for content similarity
- Clusters "same story, different source"
- Identifies cross-source duplicates

Example:
    - "Apple releases iPhone 15" (TechCrunch)
    - "New iPhone 15 unveiled by Apple" (The Verge)
    → Detected as duplicates (similarity > 0.85)
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from packages.memory.embeddings import EmbeddingService, get_embedding_service
from packages.shared.schemas import BriefItem


@dataclass
class SimilarItem:
    """Represents a similar item found in vector database"""

    fingerprint: str
    similarity: float
    title: str
    source: str
    timestamp_utc: datetime


@dataclass
class SemanticDuplicateResult:
    """Result of semantic duplicate detection"""

    is_duplicate: bool
    similar_items: List[SimilarItem]
    max_similarity: float
    reason: str


class SemanticDeduplicator:
    """
    Semantic deduplication using vector embeddings

    Architecture:
    - Qdrant vector database for fast similarity search
    - Separate collection per user
    - Text embeddings from EmbeddingService
    - Configurable similarity threshold
    """

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_threshold: float = 0.85,
        search_limit: int = 5,
    ):
        """
        Initialize semantic deduplicator

        Args:
            qdrant_url: Qdrant server URL (default: from QDRANT_URL env)
            embedding_service: Embedding service (default: auto-detect)
            similarity_threshold: Min similarity to consider duplicate (0.0-1.0)
            search_limit: Max similar items to return
        """
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.embedding_service = embedding_service or get_embedding_service()
        self.similarity_threshold = similarity_threshold
        self.search_limit = search_limit

        # Initialize Qdrant client
        self.client = QdrantClient(url=self.qdrant_url)

        # Cache embedding dimension
        self._embedding_dim = self.embedding_service.get_dimension()

    def _get_collection_name(self, user_id: str) -> str:
        """Get Qdrant collection name for user"""
        return f"user_{user_id}_items"

    def _ensure_collection_exists(self, user_id: str):
        """Create collection if it doesn't exist"""
        collection_name = self._get_collection_name(user_id)

        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self._embedding_dim,
                    distance=Distance.COSINE,
                ),
            )

    def _generate_search_text(self, item: BriefItem) -> str:
        """
        Generate searchable text from item

        Combines title + summary for better semantic matching
        """
        parts = []

        if item.title:
            parts.append(item.title)

        if item.summary:
            parts.append(item.summary)

        return " ".join(parts).strip()

    def check_duplicate(
        self, user_id: str, item: BriefItem, fingerprint: str
    ) -> SemanticDuplicateResult:
        """
        Check if item is semantically similar to existing items

        Args:
            user_id: User ID
            item: Item to check
            fingerprint: Item fingerprint

        Returns:
            SemanticDuplicateResult with duplicate status and similar items
        """
        self._ensure_collection_exists(user_id)
        collection_name = self._get_collection_name(user_id)

        # Generate search text
        search_text = self._generate_search_text(item)
        if not search_text:
            return SemanticDuplicateResult(
                is_duplicate=False,
                similar_items=[],
                max_similarity=0.0,
                reason="No searchable content",
            )

        # Generate embedding
        embedding = self.embedding_service.embed_text(search_text)

        # Search for similar items
        try:
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=embedding,
                limit=self.search_limit,
                score_threshold=self.similarity_threshold * 0.8,  # Lower threshold for search
            )
        except Exception as e:
            # Collection might be empty or not exist yet
            return SemanticDuplicateResult(
                is_duplicate=False,
                similar_items=[],
                max_similarity=0.0,
                reason=f"Search error: {str(e)}",
            )

        # Process results
        similar_items = []
        for result in search_results:
            # Skip if it's the same fingerprint
            if result.payload.get("fingerprint") == fingerprint:
                continue

            similar_item = SimilarItem(
                fingerprint=result.payload["fingerprint"],
                similarity=result.score,
                title=result.payload.get("title", ""),
                source=result.payload.get("source", ""),
                timestamp_utc=datetime.fromisoformat(result.payload["timestamp_utc"]),
            )
            similar_items.append(similar_item)

        # Determine if duplicate
        max_similarity = max([item.similarity for item in similar_items], default=0.0)
        is_duplicate = max_similarity >= self.similarity_threshold

        if is_duplicate:
            reason = f"Similar to '{similar_items[0].title}' ({similar_items[0].source}, {max_similarity:.2f})"
        elif similar_items:
            reason = f"Somewhat similar (max: {max_similarity:.2f}, threshold: {self.similarity_threshold})"
        else:
            reason = "No similar items found"

        return SemanticDuplicateResult(
            is_duplicate=is_duplicate,
            similar_items=similar_items,
            max_similarity=max_similarity,
            reason=reason,
        )

    def add_item(
        self,
        user_id: str,
        item: BriefItem,
        fingerprint: str,
    ):
        """
        Add item to vector database for future similarity checks

        Args:
            user_id: User ID
            item: Item to add
            fingerprint: Item fingerprint
        """
        self._ensure_collection_exists(user_id)
        collection_name = self._get_collection_name(user_id)

        # Generate search text and embedding
        search_text = self._generate_search_text(item)
        if not search_text:
            return  # Nothing to index

        embedding = self.embedding_service.embed_text(search_text)

        # Create point
        point = PointStruct(
            id=hash(fingerprint) & 0x7FFFFFFFFFFFFFFF,  # Convert to positive int64
            vector=embedding,
            payload={
                "fingerprint": fingerprint,
                "title": item.title,
                "source": item.source,
                "type": item.type,
                "timestamp_utc": item.timestamp_utc.isoformat(),
                "search_text": search_text[:500],  # Store excerpt for debugging
            },
        )

        # Upsert point (update if exists, create if not)
        self.client.upsert(
            collection_name=collection_name,
            points=[point],
        )

    def check_and_add(
        self, user_id: str, item: BriefItem, fingerprint: str
    ) -> SemanticDuplicateResult:
        """
        Check for duplicates and add item if not duplicate

        Convenience method that combines check_duplicate + add_item

        Args:
            user_id: User ID
            item: Item to check and add
            fingerprint: Item fingerprint

        Returns:
            SemanticDuplicateResult
        """
        result = self.check_duplicate(user_id, item, fingerprint)

        # Add to database if not duplicate
        if not result.is_duplicate:
            self.add_item(user_id, item, fingerprint)

        return result

    def batch_check_duplicates(
        self, user_id: str, items: List[Tuple[BriefItem, str]]
    ) -> List[SemanticDuplicateResult]:
        """
        Check multiple items for duplicates (batched for efficiency)

        Args:
            user_id: User ID
            items: List of (item, fingerprint) tuples

        Returns:
            List of SemanticDuplicateResults (same order as input)
        """
        results = []

        for item, fingerprint in items:
            result = self.check_duplicate(user_id, item, fingerprint)
            results.append(result)

            # Add non-duplicates to database
            if not result.is_duplicate:
                self.add_item(user_id, item, fingerprint)

        return results

    def find_cross_source_duplicates(
        self, user_id: str, items: List[BriefItem]
    ) -> Dict[str, List[BriefItem]]:
        """
        Find items that are duplicates across different sources

        Example output:
        {
            "cluster_1": [
                BriefItem(source="techcrunch", title="Apple releases..."),
                BriefItem(source="verge", title="New iPhone unveiled..."),
            ]
        }

        Args:
            user_id: User ID
            items: List of items to cluster

        Returns:
            Dict mapping cluster ID to list of similar items
        """
        clusters: Dict[str, List[BriefItem]] = {}
        processed = set()

        for i, item in enumerate(items):
            if i in processed:
                continue

            # Find similar items
            cluster = [item]
            processed.add(i)

            for j, other_item in enumerate(items[i + 1 :], start=i + 1):
                if j in processed:
                    continue

                # Calculate similarity
                text1 = self._generate_search_text(item)
                text2 = self._generate_search_text(other_item)

                if not text1 or not text2:
                    continue

                emb1 = self.embedding_service.embed_text(text1)
                emb2 = self.embedding_service.embed_text(text2)

                similarity = self.embedding_service.cosine_similarity(emb1, emb2)

                if similarity >= self.similarity_threshold:
                    cluster.append(other_item)
                    processed.add(j)

            # Only create cluster if multiple items
            if len(cluster) > 1:
                cluster_id = f"cluster_{len(clusters) + 1}"
                clusters[cluster_id] = cluster

        return clusters

    def get_stats(self, user_id: str) -> Dict:
        """
        Get statistics about user's vector database

        Returns:
            Dict with collection stats (count, size, etc.)
        """
        collection_name = self._get_collection_name(user_id)

        try:
            info = self.client.get_collection(collection_name)
            return {
                "collection_name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
            }
        except Exception:
            return {
                "collection_name": collection_name,
                "points_count": 0,
                "error": "Collection not found",
            }

    def clear_user_data(self, user_id: str):
        """Delete all vectors for user (for testing/cleanup)"""
        collection_name = self._get_collection_name(user_id)
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass  # Collection might not exist


# Singleton instance
_deduplicator_instance: Optional[SemanticDeduplicator] = None


def get_semantic_deduplicator() -> SemanticDeduplicator:
    """Get or create singleton semantic deduplicator"""
    global _deduplicator_instance
    if _deduplicator_instance is None:
        _deduplicator_instance = SemanticDeduplicator()
    return _deduplicator_instance
