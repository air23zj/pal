"""
Filesystem-based memory manager for tracking seen items.

Stores item fingerprints and metadata to enable novelty detection.

NOTE: File I/O operations are synchronous. For high-scale production use,
consider using aiofiles for async I/O or migrating to a database-backed
implementation.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ItemMemory:
    """Memory record for a single item"""
    fingerprint: str
    content_hash: str
    first_seen_utc: str
    last_seen_utc: str
    seen_count: int
    source: str
    item_type: str
    title: Optional[str] = None
    last_updated_utc: Optional[str] = None


class MemoryManager:
    """
    Filesystem-based memory manager.
    
    Stores item fingerprints and metadata in JSON files per user.
    Enables novelty detection by tracking what has been seen before.
    """
    
    def __init__(self, memory_dir: Optional[Path] = None):
        """
        Initialize memory manager.
        
        Args:
            memory_dir: Directory for memory storage (default: ./memory_store)
        """
        if memory_dir is None:
            # Default to workspace root /memory_store
            workspace_root = Path(__file__).parent.parent.parent.parent
            memory_dir = workspace_root / "memory_store"
        
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_file(self, user_id: str) -> Path:
        """Get path to user's memory file"""
        return self.memory_dir / f"{user_id}_memory.json"
    
    def _load_memory(self, user_id: str) -> Dict[str, ItemMemory]:
        """
        Load user's memory from disk.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict mapping fingerprint -> ItemMemory
        """
        file_path = self._get_user_file(user_id)
        
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert dict to ItemMemory objects
            memory = {}
            for fp, item_data in data.items():
                memory[fp] = ItemMemory(**item_data)
            
            return memory
            
        except Exception as e:
            logger.error(f"Error loading memory for {user_id}: {e}", exc_info=True)
            return {}
    
    def _save_memory(self, user_id: str, memory: Dict[str, ItemMemory]):
        """
        Save user's memory to disk.
        
        Args:
            user_id: User identifier
            memory: Memory dict to save
        """
        file_path = self._get_user_file(user_id)
        
        try:
            # Convert ItemMemory objects to dicts
            data = {fp: asdict(item_mem) for fp, item_mem in memory.items()}
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving memory for {user_id}: {e}", exc_info=True)
    
    def has_seen(self, user_id: str, fingerprint: str) -> bool:
        """
        Check if item has been seen before.
        
        Args:
            user_id: User identifier
            fingerprint: Item fingerprint
            
        Returns:
            True if item has been seen
        """
        memory = self._load_memory(user_id)
        return fingerprint in memory
    
    def get_item_memory(
        self,
        user_id: str,
        fingerprint: str,
    ) -> Optional[ItemMemory]:
        """
        Get memory record for an item.
        
        Args:
            user_id: User identifier
            fingerprint: Item fingerprint
            
        Returns:
            ItemMemory if found, None otherwise
        """
        memory = self._load_memory(user_id)
        return memory.get(fingerprint)
    
    def record_item(
        self,
        user_id: str,
        fingerprint: str,
        content_hash: str,
        source: str,
        item_type: str,
        title: Optional[str] = None,
        timestamp_utc: Optional[str] = None,
    ) -> ItemMemory:
        """
        Record an item in memory.
        
        Updates existing record or creates new one.
        
        Args:
            user_id: User identifier
            fingerprint: Item fingerprint
            content_hash: Content hash (for update detection)
            source: Source identifier
            item_type: Item type
            title: Item title
            timestamp_utc: Item timestamp
            
        Returns:
            Updated ItemMemory
        """
        memory = self._load_memory(user_id)
        now = datetime.now(timezone.utc).isoformat()
        
        if fingerprint in memory:
            # Update existing
            item_mem = memory[fingerprint]
            item_mem.last_seen_utc = now
            item_mem.seen_count += 1
            
            # Update content hash if changed
            if content_hash != item_mem.content_hash:
                item_mem.content_hash = content_hash
                item_mem.last_updated_utc = timestamp_utc or now
            
            # Update title if provided
            if title:
                item_mem.title = title
        else:
            # Create new
            item_mem = ItemMemory(
                fingerprint=fingerprint,
                content_hash=content_hash,
                first_seen_utc=now,
                last_seen_utc=now,
                seen_count=1,
                source=source,
                item_type=item_type,
                title=title,
                last_updated_utc=timestamp_utc,
            )
            memory[fingerprint] = item_mem
        
        # Save to disk
        self._save_memory(user_id, memory)
        
        return item_mem
    
    def record_items_batch(
        self,
        user_id: str,
        items: List[Dict[str, Any]],
    ) -> List[ItemMemory]:
        """
        Record multiple items in a single batch.
        
        More efficient than calling record_item multiple times.
        
        Args:
            user_id: User identifier
            items: List of item dicts with keys:
                - fingerprint
                - content_hash
                - source
                - item_type
                - title (optional)
                - timestamp_utc (optional)
                
        Returns:
            List of ItemMemory records
        """
        memory = self._load_memory(user_id)
        now = datetime.now(timezone.utc).isoformat()
        results = []
        
        for item_data in items:
            fingerprint = item_data['fingerprint']
            content_hash = item_data['content_hash']
            
            if fingerprint in memory:
                # Update existing
                item_mem = memory[fingerprint]
                item_mem.last_seen_utc = now
                item_mem.seen_count += 1
                
                if content_hash != item_mem.content_hash:
                    item_mem.content_hash = content_hash
                    item_mem.last_updated_utc = item_data.get('timestamp_utc', now)
                
                if item_data.get('title'):
                    item_mem.title = item_data['title']
            else:
                # Create new
                item_mem = ItemMemory(
                    fingerprint=fingerprint,
                    content_hash=content_hash,
                    first_seen_utc=now,
                    last_seen_utc=now,
                    seen_count=1,
                    source=item_data['source'],
                    item_type=item_data['item_type'],
                    title=item_data.get('title'),
                    last_updated_utc=item_data.get('timestamp_utc'),
                )
                memory[fingerprint] = item_mem
            
            results.append(item_mem)
        
        # Save once after all updates
        self._save_memory(user_id, memory)
        
        return results
    
    def get_all_fingerprints(self, user_id: str) -> Set[str]:
        """
        Get all fingerprints for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of fingerprints
        """
        memory = self._load_memory(user_id)
        return set(memory.keys())
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Stats dict
        """
        memory = self._load_memory(user_id)
        
        if not memory:
            return {
                'total_items': 0,
                'by_source': {},
                'by_type': {},
            }
        
        # Count by source and type
        by_source: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        
        for item_mem in memory.values():
            by_source[item_mem.source] = by_source.get(item_mem.source, 0) + 1
            by_type[item_mem.item_type] = by_type.get(item_mem.item_type, 0) + 1
        
        return {
            'total_items': len(memory),
            'by_source': by_source,
            'by_type': by_type,
        }
    
    def clear_memory(self, user_id: str):
        """
        Clear all memory for a user.
        
        Args:
            user_id: User identifier
        """
        file_path = self._get_user_file(user_id)
        
        if file_path.exists():
            file_path.unlink()
    
    def prune_old_items(
        self,
        user_id: str,
        days_to_keep: int = 90,
    ) -> int:
        """
        Remove items not seen in the last N days.
        
        Args:
            user_id: User identifier
            days_to_keep: Keep items seen within this many days
            
        Returns:
            Number of items pruned
        """
        memory = self._load_memory(user_id)
        
        if not memory:
            return 0
        
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - (days_to_keep * 24 * 3600)
        
        # Find items to remove
        to_remove = []
        for fp, item_mem in memory.items():
            last_seen = datetime.fromisoformat(item_mem.last_seen_utc.replace('Z', '+00:00'))
            if last_seen.timestamp() < cutoff:
                to_remove.append(fp)
        
        # Remove them
        for fp in to_remove:
            del memory[fp]
        
        # Save
        if to_remove:
            self._save_memory(user_id, memory)
        
        return len(to_remove)
