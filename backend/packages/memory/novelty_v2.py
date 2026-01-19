"""
Enhanced Novelty Detection (V2) - Phase 3

Combines:
1. Fingerprint-based novelty (NEW/UPDATED/REPEAT)
2. Semantic deduplication (cross-source duplicates)
3. Entity-aware updates (timeline tracking)

This provides multi-layered duplicate detection:
- Level 1: Exact fingerprint match (fast)
- Level 2: Semantic similarity (catches rephrased duplicates)
- Level 3: Entity tracking (detects meaningful updates about known topics)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from packages.shared.schemas import BriefItem, NoveltyInfo
from .novelty import NoveltyDetector, NoveltyLabel
from .semantic_dedup import SemanticDeduplicator, get_semantic_deduplicator
from .entity_tracking import EntityTracker, get_entity_tracker
from .fingerprint import generate_fingerprint


class EnhancedNoveltyLabel(str, Enum):
    """Enhanced novelty labels including semantic duplicates"""
    
    NEW = "NEW"  # Never seen before
    UPDATED = "UPDATED"  # Fingerprint match but content changed
    REPEAT = "REPEAT"  # Exact duplicate (fingerprint + content)
    SEMANTIC_DUPLICATE = "SEMANTIC_DUPLICATE"  # Different source, same story
    ENTITY_UPDATE = "ENTITY_UPDATE"  # New info about known entity


@dataclass
class EnhancedNoveltyInfo(NoveltyInfo):
    """Extended novelty info with semantic and entity details"""
    
    semantic_similarity: Optional[float] = None  # 0.0-1.0
    similar_to: Optional[str] = None  # Fingerprint of similar item
    entity_updates: Optional[List[str]] = None  # List of entity update descriptions
    duplicate_cluster: Optional[str] = None  # Cluster ID if part of duplicate group


class EnhancedNoveltyDetector:
    """
    Multi-layered novelty detection combining:
    - Fingerprint-based detection (fast, exact)
    - Semantic similarity (catches rephrasing)
    - Entity tracking (meaningful updates)
    """

    def __init__(
        self,
        novelty_detector: Optional[NoveltyDetector] = None,
        semantic_deduplicator: Optional[SemanticDeduplicator] = None,
        entity_tracker: Optional[EntityTracker] = None,
        enable_semantic: bool = True,
        enable_entity_tracking: bool = True,
    ):
        """
        Initialize enhanced novelty detector

        Args:
            novelty_detector: Base novelty detector (fingerprint-based)
            semantic_deduplicator: Semantic deduplication service
            entity_tracker: Entity tracking service
            enable_semantic: Enable semantic deduplication (default: True)
            enable_entity_tracking: Enable entity tracking (default: True)
        """
        self.base_detector = novelty_detector or NoveltyDetector()
        self.semantic_dedup = semantic_deduplicator or get_semantic_deduplicator()
        self.entity_tracker = entity_tracker or get_entity_tracker()
        self.enable_semantic = enable_semantic
        self.enable_entity_tracking = enable_entity_tracking

    def detect_novelty(
        self,
        user_id: str,
        item: BriefItem,
        item_data: Optional[Dict[str, Any]] = None,
    ) -> EnhancedNoveltyInfo:
        """
        Detect novelty with multi-layered approach

        Flow:
        1. Check fingerprint (exact duplicate)
        2. If NEW, check semantic similarity (rephrased duplicate)
        3. Track entities (meaningful updates)

        Args:
            user_id: User ID
            item: Item to check
            item_data: Optional raw item data

        Returns:
            EnhancedNoveltyInfo with complete novelty analysis
        """
        # Step 1: Fingerprint-based novelty (base layer)
        base_novelty = self.base_detector.detect_novelty(user_id, item, item_data)

        # Generate fingerprint for later use
        if item_data:
            fingerprint = generate_fingerprint(item.source, item.type, item_data)
        else:
            fingerprint = f"{item.source}:{item.item_ref}"

        # Initialize enhanced info
        enhanced_info = EnhancedNoveltyInfo(
            label=base_novelty.label,
            reason=base_novelty.reason,
            first_seen_utc=base_novelty.first_seen_utc,
            last_updated_utc=base_novelty.last_updated_utc,
            seen_count=base_novelty.seen_count,
        )

        # Step 2: Semantic deduplication (if NEW and enabled)
        if self.enable_semantic and base_novelty.label == NoveltyLabel.NEW.value:
            semantic_result = self.semantic_dedup.check_and_add(user_id, item, fingerprint)

            if semantic_result.is_duplicate:
                # Found semantic duplicate - downgrade to SEMANTIC_DUPLICATE
                enhanced_info.label = EnhancedNoveltyLabel.SEMANTIC_DUPLICATE.value
                enhanced_info.reason = semantic_result.reason
                enhanced_info.semantic_similarity = semantic_result.max_similarity

                if semantic_result.similar_items:
                    enhanced_info.similar_to = semantic_result.similar_items[0].fingerprint

        # Step 3: Entity tracking (if enabled)
        if self.enable_entity_tracking:
            entity_result = self.entity_tracker.track_item(user_id, item, fingerprint)

            if entity_result.has_updates:
                # Item contains updates about known entities
                # Upgrade label if it was REPEAT
                if enhanced_info.label == NoveltyLabel.REPEAT.value:
                    enhanced_info.label = EnhancedNoveltyLabel.ENTITY_UPDATE.value
                    enhanced_info.reason = entity_result.summary

                # Add entity update details
                enhanced_info.entity_updates = [
                    update.description for update in entity_result.entity_updates
                ]

        return enhanced_info

    def detect_novelty_batch(
        self,
        user_id: str,
        items: List[BriefItem],
        items_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[BriefItem]:
        """
        Detect novelty for multiple items with full enhancement

        Args:
            user_id: User ID
            items: List of items
            items_data: Optional raw item data

        Returns:
            Items with enhanced novelty info
        """
        # First pass: Base fingerprint novelty
        items_with_base = self.base_detector.detect_novelty_batch(user_id, items, items_data)

        # Second pass: Semantic + entity analysis
        for i, item in enumerate(items_with_base):
            item_data = items_data[i] if items_data and i < len(items_data) else None

            # Generate fingerprint
            if item_data:
                fingerprint = generate_fingerprint(item.source, item.type, item_data)
            else:
                fingerprint = f"{item.source}:{item.item_ref}"

            # Get base novelty
            base_novelty = item.novelty

            # Create enhanced info
            enhanced_info = EnhancedNoveltyInfo(
                label=base_novelty.label,
                reason=base_novelty.reason,
                first_seen_utc=base_novelty.first_seen_utc,
                last_updated_utc=base_novelty.last_updated_utc,
                seen_count=base_novelty.seen_count,
            )

            # Semantic check (if NEW and enabled)
            if self.enable_semantic and base_novelty.label == NoveltyLabel.NEW.value:
                semantic_result = self.semantic_dedup.check_and_add(user_id, item, fingerprint)

                if semantic_result.is_duplicate:
                    enhanced_info.label = EnhancedNoveltyLabel.SEMANTIC_DUPLICATE.value
                    enhanced_info.reason = semantic_result.reason
                    enhanced_info.semantic_similarity = semantic_result.max_similarity

                    if semantic_result.similar_items:
                        enhanced_info.similar_to = semantic_result.similar_items[0].fingerprint

            # Entity tracking (if enabled)
            if self.enable_entity_tracking:
                entity_result = self.entity_tracker.track_item(user_id, item, fingerprint)

                if entity_result.has_updates:
                    if enhanced_info.label == NoveltyLabel.REPEAT.value:
                        enhanced_info.label = EnhancedNoveltyLabel.ENTITY_UPDATE.value
                        enhanced_info.reason = entity_result.summary

                    enhanced_info.entity_updates = [
                        update.description for update in entity_result.entity_updates
                    ]

            # Update item with enhanced info
            item.novelty = enhanced_info

        return items_with_base

    def filter_by_novelty(
        self,
        items: List[BriefItem],
        exclude_labels: Optional[List[EnhancedNoveltyLabel]] = None,
    ) -> List[BriefItem]:
        """
        Filter items by enhanced novelty labels

        Args:
            items: Items with novelty info
            exclude_labels: Labels to exclude (default: REPEAT + SEMANTIC_DUPLICATE)

        Returns:
            Filtered items
        """
        if exclude_labels is None:
            # Default: exclude exact repeats and semantic duplicates
            exclude_labels = [
                EnhancedNoveltyLabel.REPEAT,
                EnhancedNoveltyLabel.SEMANTIC_DUPLICATE,
            ]

        exclude_strs = [label.value for label in exclude_labels]

        return [item for item in items if item.novelty and item.novelty.label not in exclude_strs]

    def find_duplicate_clusters(
        self, user_id: str, items: List[BriefItem]
    ) -> Dict[str, List[BriefItem]]:
        """
        Find cross-source duplicate clusters

        Example: Same story from TechCrunch, The Verge, and Hacker News

        Args:
            user_id: User ID
            items: List of items

        Returns:
            Dict mapping cluster_id to list of duplicate items
        """
        if not self.enable_semantic:
            return {}

        return self.semantic_dedup.find_cross_source_duplicates(user_id, items)

    def get_entity_stats(self, user_id: str) -> Dict:
        """Get entity tracking statistics"""
        if not self.enable_entity_tracking:
            return {}

        return self.entity_tracker.get_stats(user_id)

    def get_semantic_stats(self, user_id: str) -> Dict:
        """Get semantic deduplication statistics"""
        if not self.enable_semantic:
            return {}

        return self.semantic_dedup.get_stats(user_id)

    def get_novelty_stats(self, items: List[BriefItem]) -> Dict[str, int]:
        """
        Get statistics for enhanced novelty labels

        Returns:
            Dict with counts per label
        """
        stats = {
            EnhancedNoveltyLabel.NEW.value: 0,
            EnhancedNoveltyLabel.UPDATED.value: 0,
            EnhancedNoveltyLabel.REPEAT.value: 0,
            EnhancedNoveltyLabel.SEMANTIC_DUPLICATE.value: 0,
            EnhancedNoveltyLabel.ENTITY_UPDATE.value: 0,
        }

        for item in items:
            if item.novelty:
                label = item.novelty.label
                if label in stats:
                    stats[label] += 1

        return stats


def detect_novelty_enhanced(
    user_id: str,
    items: List[BriefItem],
    items_data: Optional[List[Dict[str, Any]]] = None,
    enable_semantic: bool = True,
    enable_entity_tracking: bool = True,
    exclude_duplicates: bool = True,
) -> List[BriefItem]:
    """
    Convenience function for enhanced novelty detection

    Args:
        user_id: User ID
        items: Items to check
        items_data: Optional raw item data
        enable_semantic: Enable semantic deduplication
        enable_entity_tracking: Enable entity tracking
        exclude_duplicates: Filter out REPEAT and SEMANTIC_DUPLICATE

    Returns:
        Items with enhanced novelty info (optionally filtered)
    """
    detector = EnhancedNoveltyDetector(
        enable_semantic=enable_semantic,
        enable_entity_tracking=enable_entity_tracking,
    )

    # Detect novelty
    items_with_novelty = detector.detect_novelty_batch(user_id, items, items_data)

    # Filter if requested
    if exclude_duplicates:
        items_with_novelty = detector.filter_by_novelty(items_with_novelty)

    return items_with_novelty
