"""
Novelty detection system.

Labels items as NEW, UPDATED, or REPEAT based on memory.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from packages.shared.schemas import BriefItem, NoveltyInfo
from .memory_manager import MemoryManager, ItemMemory
from .fingerprint import generate_fingerprint, content_hash


class NoveltyLabel(str, Enum):
    """Novelty labels for items"""
    NEW = "NEW"         # Never seen before
    UPDATED = "UPDATED"  # Seen before, but content changed
    REPEAT = "REPEAT"    # Seen before, no change


class NoveltyDetector:
    """
    Detects novelty for items using memory system.
    
    Labels each item as NEW, UPDATED, or REPEAT.
    """
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize novelty detector.
        
        Args:
            memory_manager: Memory manager instance (default: creates new)
        """
        self.memory = memory_manager or MemoryManager()
    
    def detect_novelty(
        self,
        user_id: str,
        item: BriefItem,
        item_data: Optional[Dict[str, Any]] = None,
    ) -> NoveltyInfo:
        """
        Detect novelty for a single item.
        
        Args:
            user_id: User identifier
            item: BriefItem to check
            item_data: Optional raw item data for fingerprinting
            
        Returns:
            NoveltyInfo with label and reason
        """
        # Generate fingerprint
        if item_data:
            fingerprint = generate_fingerprint(
                source=item.source,
                item_type=item.type,
                item_data=item_data,
            )
            c_hash = content_hash(item_data)
        else:
            # Fallback: use item_ref as fingerprint
            fingerprint = f"{item.source}:{item.item_ref}"
            # Generate content hash from item fields
            c_hash = content_hash({
                'title': item.title,
                'summary': item.summary,
                'timestamp': item.timestamp_utc,
            })
        
        # Check memory
        item_mem = self.memory.get_item_memory(user_id, fingerprint)
        
        if item_mem is None:
            # Never seen before
            label = NoveltyLabel.NEW
            reason = "First time seeing this item"
            first_seen_utc = datetime.now(timezone.utc).isoformat()
        
        elif item_mem.content_hash != c_hash:
            # Content changed
            label = NoveltyLabel.UPDATED
            reason = f"Content changed since {item_mem.last_seen_utc}"
            first_seen_utc = item_mem.first_seen_utc
        
        else:
            # No change
            label = NoveltyLabel.REPEAT
            reason = f"Seen {item_mem.seen_count} times, last on {item_mem.last_seen_utc}"
            first_seen_utc = item_mem.first_seen_utc
        
        # Record in memory
        self.memory.record_item(
            user_id=user_id,
            fingerprint=fingerprint,
            content_hash=c_hash,
            source=item.source,
            item_type=item.type,
            title=item.title,
            timestamp_utc=item.timestamp_utc,
        )
        
        return NoveltyInfo(
            label=label.value,
            reason=reason,
            first_seen_utc=first_seen_utc,
        )
    
    def detect_novelty_batch(
        self,
        user_id: str,
        items: List[BriefItem],
        items_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[BriefItem]:
        """
        Detect novelty for multiple items efficiently.
        
        Args:
            user_id: User identifier
            items: List of BriefItems
            items_data: Optional list of raw item data (same order as items)
            
        Returns:
            Items with novelty info added
        """
        # Prepare batch data for memory recording
        memory_records = []
        novelty_infos = []
        
        for i, item in enumerate(items):
            # Get item data if available
            item_data = items_data[i] if items_data and i < len(items_data) else None
            
            # Generate fingerprint and content hash
            if item_data:
                fingerprint = generate_fingerprint(
                    source=item.source,
                    item_type=item.type,
                    item_data=item_data,
                )
                c_hash = content_hash(item_data)
            else:
                fingerprint = f"{item.source}:{item.item_ref}"
                c_hash = content_hash({
                    'title': item.title,
                    'summary': item.summary,
                    'timestamp': item.timestamp_utc,
                })
            
            # Check memory
            item_mem = self.memory.get_item_memory(user_id, fingerprint)
            
            if item_mem is None:
                label = NoveltyLabel.NEW
                reason = "First time seeing this item"
                first_seen_utc = datetime.now(timezone.utc).isoformat()
            
            elif item_mem.content_hash != c_hash:
                label = NoveltyLabel.UPDATED
                reason = f"Content changed since {item_mem.last_seen_utc}"
                first_seen_utc = item_mem.first_seen_utc
            
            else:
                label = NoveltyLabel.REPEAT
                reason = f"Seen {item_mem.seen_count} times, last on {item_mem.last_seen_utc}"
                first_seen_utc = item_mem.first_seen_utc
            
            # Store for batch recording
            memory_records.append({
                'fingerprint': fingerprint,
                'content_hash': c_hash,
                'source': item.source,
                'item_type': item.type,
                'title': item.title,
                'timestamp_utc': item.timestamp_utc,
            })
            
            novelty_infos.append(NoveltyInfo(
                label=label.value,
                reason=reason,
                first_seen_utc=first_seen_utc,
            ))
        
        # Record all items in memory (single write)
        self.memory.record_items_batch(user_id, memory_records)
        
        # Update items with novelty info
        for item, novelty_info in zip(items, novelty_infos):
            item.novelty = novelty_info
        
        return items
    
    def filter_by_novelty(
        self,
        items: List[BriefItem],
        exclude_labels: Optional[List[NoveltyLabel]] = None,
    ) -> List[BriefItem]:
        """
        Filter items by novelty label.
        
        Args:
            items: List of items with novelty info
            exclude_labels: Labels to exclude (default: [REPEAT])
            
        Returns:
            Filtered items
        """
        if exclude_labels is None:
            exclude_labels = [NoveltyLabel.REPEAT]
        
        exclude_strs = [label.value for label in exclude_labels]
        
        return [
            item for item in items
            if item.novelty and item.novelty.label not in exclude_strs
        ]
    
    def get_novelty_stats(
        self,
        items: List[BriefItem],
    ) -> Dict[str, int]:
        """
        Get novelty statistics for a list of items.
        
        Args:
            items: List of items with novelty info
            
        Returns:
            Dict with counts per label
        """
        stats = {
            NoveltyLabel.NEW.value: 0,
            NoveltyLabel.UPDATED.value: 0,
            NoveltyLabel.REPEAT.value: 0,
        }
        
        for item in items:
            if item.novelty:
                label = item.novelty.label
                if label in stats:
                    stats[label] += 1
        
        return stats


def detect_novelty_for_items(
    user_id: str,
    items: List[BriefItem],
    items_data: Optional[List[Dict[str, Any]]] = None,
    memory_manager: Optional[MemoryManager] = None,
    exclude_repeats: bool = True,
) -> List[BriefItem]:
    """
    Convenience function to detect novelty and optionally filter repeats.
    
    Args:
        user_id: User identifier
        items: List of BriefItems
        items_data: Optional raw item data
        memory_manager: Optional memory manager
        exclude_repeats: If True, filter out REPEAT items
        
    Returns:
        Items with novelty labels (optionally filtered)
    """
    detector = NoveltyDetector(memory_manager)
    
    # Detect novelty
    items_with_novelty = detector.detect_novelty_batch(
        user_id=user_id,
        items=items,
        items_data=items_data,
    )
    
    # Filter if requested
    if exclude_repeats:
        items_with_novelty = detector.filter_by_novelty(
            items_with_novelty,
            exclude_labels=[NoveltyLabel.REPEAT],
        )
    
    return items_with_novelty
