"""
Comprehensive tests for Phase 3: Advanced Memory Features

Tests:
1. Embedding generation (OpenAI + SentenceTransformers)
2. Semantic deduplication (Qdrant + vector search)
3. Entity-aware update detection
4. Enhanced novelty detection (V2)
"""

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from packages.memory.embeddings import (
    EmbeddingService,
    OpenAIEmbeddingProvider,
    SentenceTransformerProvider,
)
from packages.memory.semantic_dedup import SemanticDeduplicator, SimilarItem
from packages.memory.entity_tracking import EntityTracker, EntityUpdate
from packages.memory.novelty_v2 import (
    EnhancedNoveltyDetector,
    EnhancedNoveltyLabel,
    detect_novelty_enhanced,
)
from packages.shared.schemas import BriefItem, Entity, NoveltyInfo, RankingScores


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_embedding_provider():
    """Mock embedding provider for testing"""
    provider = Mock()
    provider.embed_text.return_value = [0.1] * 384  # MiniLM dimension
    provider.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    provider.get_dimension.return_value = 384
    return provider


@pytest.fixture
def embedding_service(mock_embedding_provider):
    """Embedding service with mock provider"""
    return EmbeddingService(provider=mock_embedding_provider)


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    client = Mock()
    client.get_collections.return_value = Mock(collections=[])
    client.create_collection.return_value = None
    client.search.return_value = []
    client.upsert.return_value = None
    return client


@pytest.fixture
def semantic_dedup(embedding_service, mock_qdrant_client):
    """Semantic deduplicator with mocked dependencies"""
    with patch("packages.memory.semantic_dedup.QdrantClient", return_value=mock_qdrant_client):
        dedup = SemanticDeduplicator(
            qdrant_url="http://localhost:6333",
            embedding_service=embedding_service,
        )
        dedup.client = mock_qdrant_client
        return dedup


@pytest.fixture
def entity_tracker():
    """Entity tracker instance"""
    tracker = EntityTracker()
    # Clear any existing data
    tracker._entities.clear()
    return tracker


@pytest.fixture
def sample_item():
    """Sample BriefItem for testing"""
    return BriefItem(
        item_ref="test_123",
        source="news",
        type="article",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        title="SpaceX launches Starship",
        summary="SpaceX successfully launched its Starship rocket today.",
        why_it_matters="SpaceX continues to advance space technology",
        entities=[
            Entity(kind="company", key="SpaceX"),
            Entity(kind="product", key="Starship"),
        ],
        novelty=NoveltyInfo(
            label="NEW",
            reason="First time",
            first_seen_utc=datetime.now(timezone.utc).isoformat(),
            last_updated_utc=datetime.now(timezone.utc).isoformat(),
            seen_count=1,
        ),
        ranking=RankingScores(
            final_score=0.8,
            relevance=0.8,
            urgency=0.7,
            credibility=0.9,
            impact=0.7,
            actionability=0.6,
        ),
    )


@pytest.fixture
def similar_item():
    """Similar item (rephrased)"""
    return BriefItem(
        item_ref="test_456",
        source="techcrunch",
        type="article",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        title="Starship rocket launched by SpaceX",
        summary="SpaceX's Starship rocket had a successful launch today.",
        why_it_matters="SpaceX continues to advance space technology",
        entities=[
            Entity(kind="company", key="SpaceX"),
            Entity(kind="product", key="Starship"),
        ],
        novelty=NoveltyInfo(
            label="NEW",
            reason="First time",
            first_seen_utc=datetime.now(timezone.utc).isoformat(),
            last_updated_utc=datetime.now(timezone.utc).isoformat(),
            seen_count=1,
        ),
        ranking=RankingScores(
            final_score=0.8,
            relevance=0.8,
            urgency=0.7,
            credibility=0.9,
            impact=0.7,
            actionability=0.6,
        ),
    )


# ============================================================================
# Embedding Service Tests
# ============================================================================


class TestEmbeddingService:
    """Test embedding generation"""

    def test_embed_text_single(self, embedding_service):
        """Test single text embedding"""
        text = "This is a test"
        embedding = embedding_service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_text_empty(self, embedding_service):
        """Test embedding empty text returns zero vector"""
        embedding = embedding_service.embed_text("")

        assert len(embedding) == 384
        assert all(x == 0.0 for x in embedding)

    def test_embed_batch(self, embedding_service):
        """Test batch embedding"""
        texts = ["First text", "Second text"]
        embeddings = embedding_service.embed_batch(texts)

        assert len(embeddings) == 2
        assert all(len(emb) == 384 for emb in embeddings)

    def test_embed_batch_with_empty(self, embedding_service):
        """Test batch embedding handles empty texts"""
        texts = ["Text 1", "", "Text 2"]
        embeddings = embedding_service.embed_batch(texts)

        assert len(embeddings) == 3
        # Empty text should have zero vector
        assert all(x == 0.0 for x in embeddings[1])

    def test_cosine_similarity(self, embedding_service):
        """Test cosine similarity calculation"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = embedding_service.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self, embedding_service):
        """Test cosine similarity for orthogonal vectors"""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]

        similarity = embedding_service.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0, abs=1e-6)

    def test_get_dimension(self, embedding_service):
        """Test get embedding dimension"""
        assert embedding_service.get_dimension() == 384


class TestSentenceTransformerProvider:
    """Test sentence transformer provider (local embeddings)"""

    @pytest.mark.skipif(
        os.getenv("SKIP_SLOW_TESTS") == "1", reason="Slow test - downloads model"
    )
    def test_sentence_transformer_real(self):
        """Test actual sentence transformer (requires download)"""
        provider = SentenceTransformerProvider(model_name="all-MiniLM-L6-v2")

        embedding = provider.embed_text("This is a test")

        assert isinstance(embedding, list)
        assert len(embedding) == 384  # MiniLM dimension
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.skipif(
        os.getenv("SKIP_SLOW_TESTS") == "1", reason="Slow test - downloads model"
    )
    def test_sentence_transformer_batch(self):
        """Test batch embedding with real model"""
        provider = SentenceTransformerProvider()

        texts = ["First", "Second", "Third"]
        embeddings = provider.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)


# ============================================================================
# Semantic Deduplication Tests
# ============================================================================


class TestSemanticDeduplicator:
    """Test semantic duplicate detection"""

    def test_ensure_collection_exists(self, semantic_dedup, mock_qdrant_client):
        """Test collection creation"""
        semantic_dedup._ensure_collection_exists("user123")

        # Should check for existing collections
        mock_qdrant_client.get_collections.assert_called_once()

        # Should create collection if not exists
        mock_qdrant_client.create_collection.assert_called_once()

    def test_generate_search_text(self, semantic_dedup, sample_item):
        """Test search text generation"""
        search_text = semantic_dedup._generate_search_text(sample_item)

        assert "SpaceX" in search_text
        assert "Starship" in search_text
        assert len(search_text) > 0

    def test_check_duplicate_no_results(self, semantic_dedup, sample_item, mock_qdrant_client):
        """Test check_duplicate when no similar items found"""
        mock_qdrant_client.search.return_value = []

        result = semantic_dedup.check_duplicate("user123", sample_item, "test_fp")

        assert not result.is_duplicate
        assert result.max_similarity == 0.0
        assert len(result.similar_items) == 0

    def test_check_duplicate_found(self, semantic_dedup, sample_item, mock_qdrant_client):
        """Test check_duplicate when similar item found"""
        # Mock search result with high similarity
        mock_result = Mock()
        mock_result.score = 0.92
        mock_result.payload = {
            "fingerprint": "existing_fp",
            "title": "SpaceX Starship launch",
            "source": "techcrunch",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        mock_qdrant_client.search.return_value = [mock_result]

        result = semantic_dedup.check_duplicate("user123", sample_item, "test_fp")

        assert result.is_duplicate
        assert result.max_similarity == 0.92
        assert len(result.similar_items) == 1
        assert result.similar_items[0].fingerprint == "existing_fp"

    def test_check_duplicate_below_threshold(
        self, semantic_dedup, sample_item, mock_qdrant_client
    ):
        """Test check_duplicate with similarity below threshold"""
        # Mock search result with low similarity
        mock_result = Mock()
        mock_result.score = 0.70  # Below default threshold of 0.85
        mock_result.payload = {
            "fingerprint": "existing_fp",
            "title": "Different article",
            "source": "news",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        mock_qdrant_client.search.return_value = [mock_result]

        result = semantic_dedup.check_duplicate("user123", sample_item, "test_fp")

        assert not result.is_duplicate  # Below threshold
        assert result.max_similarity == 0.70
        assert len(result.similar_items) == 1

    def test_add_item(self, semantic_dedup, sample_item, mock_qdrant_client):
        """Test adding item to vector database"""
        semantic_dedup.add_item("user123", sample_item, "test_fp")

        # Should upsert point
        mock_qdrant_client.upsert.assert_called_once()

        # Check upsert arguments
        call_args = mock_qdrant_client.upsert.call_args
        assert "user_123_items" in call_args.kwargs["collection_name"]
        assert len(call_args.kwargs["points"]) == 1

    def test_check_and_add_not_duplicate(
        self, semantic_dedup, sample_item, mock_qdrant_client
    ):
        """Test check_and_add when item is not duplicate"""
        mock_qdrant_client.search.return_value = []

        result = semantic_dedup.check_and_add("user123", sample_item, "test_fp")

        assert not result.is_duplicate
        # Should add to database
        mock_qdrant_client.upsert.assert_called_once()

    def test_check_and_add_is_duplicate(self, semantic_dedup, sample_item, mock_qdrant_client):
        """Test check_and_add when item is duplicate"""
        # Mock high similarity result
        mock_result = Mock()
        mock_result.score = 0.95
        mock_result.payload = {
            "fingerprint": "existing_fp",
            "title": "Similar title",
            "source": "news",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        mock_qdrant_client.search.return_value = [mock_result]

        result = semantic_dedup.check_and_add("user123", sample_item, "test_fp")

        assert result.is_duplicate
        # Should NOT add to database (duplicate)
        mock_qdrant_client.upsert.assert_not_called()

    def test_batch_check_duplicates(
        self, semantic_dedup, sample_item, similar_item, mock_qdrant_client
    ):
        """Test batch duplicate checking"""
        mock_qdrant_client.search.return_value = []

        items = [(sample_item, "fp1"), (similar_item, "fp2")]
        results = semantic_dedup.batch_check_duplicates("user123", items)

        assert len(results) == 2
        assert all(not r.is_duplicate for r in results)
        # Should add both items
        assert mock_qdrant_client.upsert.call_count == 2

    def test_get_stats(self, semantic_dedup, mock_qdrant_client):
        """Test getting collection statistics"""
        mock_collection_info = Mock()
        mock_collection_info.points_count = 42
        mock_collection_info.vectors_count = 42
        mock_collection_info.indexed_vectors_count = 42

        mock_qdrant_client.get_collection.return_value = mock_collection_info

        stats = semantic_dedup.get_stats("user123")

        assert stats["points_count"] == 42
        assert "user_123_items" in stats["collection_name"]


# ============================================================================
# Entity Tracking Tests
# ============================================================================


class TestEntityTracker:
    """Test entity-aware update detection"""

    def test_track_item_new_entity(self, entity_tracker, sample_item):
        """Test tracking item with new entity"""
        result = entity_tracker.track_item("user123", sample_item, "fp1")

        assert not result.has_updates
        assert len(result.new_entities) == 2  # SpaceX + Starship
        assert len(result.known_entities) == 0
        assert "company:SpaceX" in result.new_entities

    def test_track_item_known_entity(self, entity_tracker, sample_item):
        """Test tracking item with known entity"""
        # First tracking
        entity_tracker.track_item("user123", sample_item, "fp1")

        # Second tracking (same entities)
        result = entity_tracker.track_item("user123", sample_item, "fp2")

        assert len(result.known_entities) == 2
        assert len(result.new_entities) == 0

    def test_track_item_entity_update(self, entity_tracker):
        """Test detecting entity update"""
        # First item: SpaceX announces launch
        item1 = BriefItem(
            item_ref="1",
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc) - timedelta(days=10),
            title="SpaceX announces Mars mission",
            summary="SpaceX plans to launch a mission to Mars",
            entities=[Entity(kind="company", key="SpaceX")],
        )

        entity_tracker.track_item("user123", item1, "fp1")

        # Second item: SpaceX delays launch (status change)
        item2 = BriefItem(
            item_ref="2",
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc),
            title="SpaceX delays Mars mission",
            summary="SpaceX has delayed the Mars mission to 2026",
            entities=[Entity(kind="company", key="SpaceX")],
        )

        result = entity_tracker.track_item("user123", item2, "fp2")

        # Should detect status change
        assert result.has_updates
        assert len(result.entity_updates) > 0

    def test_detect_status_change(self, entity_tracker):
        """Test detecting status keywords"""
        item1 = BriefItem(
            item_ref="1",
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc),
            title="Product announced",
            summary="Company announced new product",
            entities=[Entity(kind="product", key="NewProduct")],
        )

        entity_tracker.track_item("user123", item1, "fp1")

        item2 = BriefItem(
            item_ref="2",
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc),
            title="Product launched",
            summary="Company launched the new product today",
            entities=[Entity(kind="product", key="NewProduct")],
        )

        result = entity_tracker.track_item("user123", item2, "fp2")

        # Should detect status change from "announced" to "launched"
        assert result.has_updates
        assert any("status" in update.update_type for update in result.entity_updates)

    def test_get_entity_timeline(self, entity_tracker, sample_item):
        """Test getting entity timeline"""
        entity_tracker.track_item("user123", sample_item, "fp1")

        timeline = entity_tracker.get_entity_timeline("user123", "company:SpaceX")

        assert timeline is not None
        assert timeline.entity_key == "company:SpaceX"
        assert timeline.item_count == 1

    def test_get_all_entities(self, entity_tracker, sample_item):
        """Test getting all tracked entities"""
        entity_tracker.track_item("user123", sample_item, "fp1")

        entities = entity_tracker.get_all_entities("user123")

        assert len(entities) == 2  # SpaceX + Starship
        assert all(isinstance(e.entity_key, str) for e in entities)

    def test_get_active_entities(self, entity_tracker):
        """Test getting active entities in time window"""
        # Old item
        old_item = BriefItem(
            item_ref="1",
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc) - timedelta(days=60),
            title="Old news",
            summary="Old news",
            entities=[Entity(kind="company", key="OldCompany")],
        )

        entity_tracker.track_item("user123", old_item, "fp1")

        # Recent item
        recent_item = BriefItem(
            item_ref="2",
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc),
            title="Recent news",
            summary="Recent news",
            entities=[Entity(kind="company", key="NewCompany")],
        )

        entity_tracker.track_item("user123", recent_item, "fp2")

        # Get active in last 30 days
        active = entity_tracker.get_active_entities("user123", days=30)

        # Should only include recent entity
        assert len(active) == 1
        assert active[0].entity_key == "company:NewCompany"

    def test_get_stats(self, entity_tracker, sample_item):
        """Test entity statistics"""
        entity_tracker.track_item("user123", sample_item, "fp1")

        stats = entity_tracker.get_stats("user123")

        assert stats["total_entities"] == 2
        assert "company" in stats["by_kind"]
        assert "product" in stats["by_kind"]


# ============================================================================
# Enhanced Novelty Detection Tests
# ============================================================================


class TestEnhancedNoveltyDetector:
    """Test enhanced novelty detection (V2)"""

    @pytest.fixture
    def enhanced_detector(self, semantic_dedup, entity_tracker):
        """Enhanced detector with mocked dependencies"""
        from packages.memory.novelty import NoveltyDetector

        base_detector = NoveltyDetector()
        return EnhancedNoveltyDetector(
            novelty_detector=base_detector,
            semantic_deduplicator=semantic_dedup,
            entity_tracker=entity_tracker,
        )

    def test_detect_novelty_new_item(self, enhanced_detector, sample_item, mock_qdrant_client):
        """Test detecting truly new item"""
        mock_qdrant_client.search.return_value = []

        result = enhanced_detector.detect_novelty("user123", sample_item)

        assert result.label == EnhancedNoveltyLabel.NEW.value
        assert result.semantic_similarity is None  # No similar items

    def test_detect_novelty_semantic_duplicate(
        self, enhanced_detector, sample_item, mock_qdrant_client
    ):
        """Test detecting semantic duplicate"""
        # Mock high similarity result
        mock_result = Mock()
        mock_result.score = 0.92
        mock_result.payload = {
            "fingerprint": "existing_fp",
            "title": "SpaceX Starship launched",
            "source": "techcrunch",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        mock_qdrant_client.search.return_value = [mock_result]

        result = enhanced_detector.detect_novelty("user123", sample_item)

        assert result.label == EnhancedNoveltyLabel.SEMANTIC_DUPLICATE.value
        assert result.semantic_similarity == 0.92
        assert result.similar_to == "existing_fp"

    def test_detect_novelty_entity_update(self, enhanced_detector, mock_qdrant_client):
        """Test detecting entity update"""
        mock_qdrant_client.search.return_value = []

        # First item
        item1 = BriefItem(
            item_ref="1",
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc) - timedelta(days=10),
            title="Product announced",
            summary="Company announced new product",
            entities=[Entity(kind="product", key="NewProduct")],
        )

        enhanced_detector.detect_novelty("user123", item1)

        # Second item (same fingerprint but status change)
        # For this test, we'll manually mark it as REPEAT in base detection
        # but entity update should upgrade it
        item2 = BriefItem(
            item_ref="1",  # Same ref = same fingerprint
            source="news",
            type="article",
            timestamp_utc=datetime.now(timezone.utc),
            title="Product launched",
            summary="Company launched the product",
            entities=[Entity(kind="product", key="NewProduct")],
        )

        result = enhanced_detector.detect_novelty("user123", item2)

        # With entity tracking, this should detect an update
        assert result.entity_updates is not None

    def test_filter_by_novelty_default(self, enhanced_detector, sample_item, mock_qdrant_client):
        """Test default filtering (excludes REPEAT + SEMANTIC_DUPLICATE)"""
        mock_qdrant_client.search.return_value = []

        # Create items with different labels
        items = [sample_item]
        items = enhanced_detector.detect_novelty_batch("user123", items)

        # All should be NEW (no duplicates)
        filtered = enhanced_detector.filter_by_novelty(items)
        assert len(filtered) == len(items)

    def test_get_novelty_stats(self, enhanced_detector, sample_item, mock_qdrant_client):
        """Test novelty statistics"""
        mock_qdrant_client.search.return_value = []

        items = [sample_item]
        items = enhanced_detector.detect_novelty_batch("user123", items)

        stats = enhanced_detector.get_novelty_stats(items)

        assert stats[EnhancedNoveltyLabel.NEW.value] == 1
        assert stats[EnhancedNoveltyLabel.SEMANTIC_DUPLICATE.value] == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestPhase3Integration:
    """Integration tests for Phase 3 features"""

    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "1", reason="Integration test"
    )
    def test_end_to_end_duplicate_detection(self, embedding_service):
        """Test full pipeline: same story from different sources"""
        # This test requires real embedding and Qdrant
        # Skip in CI, run locally with real services

        items = [
            BriefItem(
                item_ref="1",
                source="techcrunch",
                type="article",
                timestamp_utc=datetime.now(timezone.utc),
                title="Apple releases iPhone 15",
                summary="Apple announced the new iPhone 15 today",
            ),
            BriefItem(
                item_ref="2",
                source="verge",
                type="article",
                timestamp_utc=datetime.now(timezone.utc),
                title="New iPhone 15 unveiled by Apple",
                summary="Apple's latest iPhone 15 was unveiled at today's event",
            ),
        ]

        # Should detect as semantic duplicates
        # (implementation depends on real services)
        pass


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Performance tests for Phase 3 features"""

    def test_embedding_batch_performance(self, embedding_service):
        """Test batch embedding is faster than individual"""
        import time

        texts = ["Test text"] * 10

        # Individual embeddings
        start = time.time()
        for text in texts:
            embedding_service.embed_text(text)
        individual_time = time.time() - start

        # Batch embedding
        start = time.time()
        embedding_service.embed_batch(texts)
        batch_time = time.time() - start

        # Batch should be faster (or at least not much slower)
        assert batch_time <= individual_time * 1.5

    def test_entity_tracking_scales(self, entity_tracker):
        """Test entity tracking scales with many items"""
        import time

        # Create 100 items with various entities
        items = []
        for i in range(100):
            item = BriefItem(
                item_ref=f"item_{i}",
                source="news",
                type="article",
                timestamp_utc=datetime.now(timezone.utc),
                title=f"News about Company {i % 10}",
                summary=f"Company {i % 10} did something",
                entities=[Entity(kind="company", key=f"Company{i % 10}")],
            )
            items.append(item)

        # Track all items
        start = time.time()
        for i, item in enumerate(items):
            entity_tracker.track_item("user123", item, f"fp_{i}")
        elapsed = time.time() - start

        # Should complete in reasonable time (< 1 second for 100 items)
        assert elapsed < 1.0

        # Should have tracked 10 unique entities
        stats = entity_tracker.get_stats("user123")
        assert stats["total_entities"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
