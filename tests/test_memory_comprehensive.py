"""
Comprehensive tests for Memory module - Target 90%+ coverage
"""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
from packages.memory.fingerprint import generate_fingerprint, content_hash
from packages.memory.novelty import NoveltyDetector, NoveltyLabel
from packages.memory.memory_manager import MemoryManager
from packages.shared.schemas import BriefItem, NoveltyInfo, RankingScores, Entity


@pytest.fixture
def sample_brief_item():
    """Create a sample BriefItem for testing"""
    return BriefItem(
        item_ref='test_item_1',
        source='gmail',
        type='email',
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        title='Test Email',
        summary='Test summary',
        why_it_matters='Test',
        entities=[],
        novelty=NoveltyInfo(
            label='NEW',
            reason='Test',
            first_seen_utc=datetime.now(timezone.utc).isoformat()
        ),
        ranking=RankingScores(
            relevance_score=0.5,
            urgency_score=0.5,
            credibility_score=0.5,
            impact_score=0.5,
            actionability_score=0.5,
            final_score=0.5
        ),
        evidence=[],
        suggested_actions=[]
    )


class TestFingerprint:
    """Test fingerprint generation"""
    
    def test_generate_fingerprint_basic(self):
        """Test basic fingerprint generation"""
        fp = generate_fingerprint('gmail', 'email', {'id': 'msg1', 'title': 'Test'})
        assert isinstance(fp, str)
        assert len(fp) > 0
        
    def test_generate_fingerprint_consistency(self):
        """Test fingerprint consistency"""
        data = {'id': 'msg1', 'title': 'Test'}
        fp1 = generate_fingerprint('gmail', 'email', data)
        fp2 = generate_fingerprint('gmail', 'email', data)
        assert fp1 == fp2
        
    def test_generate_fingerprint_uniqueness(self):
        """Test fingerprint uniqueness"""
        fp1 = generate_fingerprint('gmail', 'email', {'id': 'msg1'})
        fp2 = generate_fingerprint('gmail', 'email', {'id': 'msg2'})
        assert fp1 != fp2
        
    def test_generate_fingerprint_different_sources(self):
        """Test fingerprints differ by source"""
        data = {'id': 'item1'}
        fp1 = generate_fingerprint('gmail', 'email', data)
        fp2 = generate_fingerprint('calendar', 'event', data)
        assert fp1 != fp2
        
    def test_content_hash_basic(self):
        """Test basic content hashing"""
        data = {'title': 'Test', 'content': 'Content'}
        hash1 = content_hash(data)
        assert isinstance(hash1, str)
        assert len(hash1) > 0
        
    def test_content_hash_consistency(self):
        """Test content hash consistency"""
        data = {'title': 'Test', 'content': 'Content'}
        hash1 = content_hash(data)
        hash2 = content_hash(data)
        assert hash1 == hash2
        
    def test_content_hash_detects_changes(self):
        """Test content hash detects changes"""
        data1 = {'title': 'Test', 'content': 'Content 1'}
        data2 = {'title': 'Test', 'content': 'Content 2'}
        hash1 = content_hash(data1)
        hash2 = content_hash(data2)
        assert hash1 != hash2
        
    def test_content_hash_empty_data(self):
        """Test content hash with empty data"""
        hash_val = content_hash({})
        assert isinstance(hash_val, str)
        
    def test_content_hash_with_nested_data(self):
        """Test content hash with nested structures"""
        data = {
            'title': 'Test',
            'metadata': {'author': 'user', 'tags': ['tag1', 'tag2']}
        }
        hash_val = content_hash(data)
        assert isinstance(hash_val, str)


class TestNoveltyDetector:
    """Test NoveltyDetector"""
    
    def test_novelty_detector_init(self, tmp_path):
        """Test novelty detector initialization"""
        manager = MemoryManager(memory_dir=tmp_path)
        detector = NoveltyDetector(memory_manager=manager)
        assert detector is not None
        
    def test_novelty_detector_init_default(self):
        """Test novelty detector with default manager"""
        detector = NoveltyDetector()
        assert detector is not None
        
    def test_detect_new_item(self, tmp_path, sample_brief_item):
        """Test detecting NEW item"""
        manager = MemoryManager(memory_dir=tmp_path)
        detector = NoveltyDetector(memory_manager=manager)
        
        item_data = {'id': 'msg1', 'title': 'Test'}
        novelty_info = detector.detect_novelty('user1', sample_brief_item, item_data)
        
        assert novelty_info.label == 'NEW'
        
    def test_detect_repeat_item(self, tmp_path, sample_brief_item):
        """Test detecting REPEAT item"""
        manager = MemoryManager(memory_dir=tmp_path)
        detector = NoveltyDetector(memory_manager=manager)
        
        item_data = {'id': 'msg1', 'title': 'Test'}
        
        # First time - NEW
        novelty1 = detector.detect_novelty('user1', sample_brief_item, item_data)
        assert novelty1.label == 'NEW'
        
        # Second time - REPEAT
        novelty2 = detector.detect_novelty('user1', sample_brief_item, item_data)
        assert novelty2.label == 'REPEAT'
        
    def test_detect_updated_item(self, tmp_path, sample_brief_item):
        """Test detecting UPDATED item"""
        manager = MemoryManager(memory_dir=tmp_path)
        detector = NoveltyDetector(memory_manager=manager)
        
        item_data1 = {'id': 'msg1', 'title': 'Original'}
        item_data2 = {'id': 'msg1', 'title': 'Updated'}
        
        # First time - NEW
        novelty1 = detector.detect_novelty('user1', sample_brief_item, item_data1)
        assert novelty1.label == 'NEW'
        
        # Same fingerprint, different content - UPDATED
        novelty2 = detector.detect_novelty('user1', sample_brief_item, item_data2)
        assert novelty2.label == 'UPDATED'
        
    def test_novelty_user_isolation(self, tmp_path):
        """Test that novelty is user-specific"""
        manager = MemoryManager(memory_dir=tmp_path)
        detector = NoveltyDetector(memory_manager=manager)
        
        item1 = BriefItem(
            item_ref='item1',
            source='gmail',
            type='email',
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            title='Test',
            summary='Test',
            why_it_matters='Test',
            entities=[],
            novelty=NoveltyInfo(label='NEW', reason='Test', first_seen_utc=datetime.now(timezone.utc).isoformat()),
            ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, impact_score=0.5, actionability_score=0.5, final_score=0.5),
            evidence=[],
            suggested_actions=[]
        )
        
        item_data = {'id': 'msg1', 'title': 'Test'}
        
        # User 1 sees it as NEW
        novelty1 = detector.detect_novelty('user1', item1, item_data)
        assert novelty1.label == 'NEW'
        
        # User 2 also sees it as NEW (isolated)
        novelty2 = detector.detect_novelty('user2', item1, item_data)
        assert novelty2.label == 'NEW'
        
    def test_detect_novelty_batch(self, tmp_path):
        """Test batch novelty detection"""
        manager = MemoryManager(memory_dir=tmp_path)
        detector = NoveltyDetector(memory_manager=manager)
        
        items = []
        items_data = []
        for i in range(3):
            item = BriefItem(
                item_ref=f'item_{i}',
                source='gmail',
                type='email',
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                title=f'Test {i}',
                summary=f'Summary {i}',
                why_it_matters='Test',
                entities=[],
                novelty=NoveltyInfo(label='NEW', reason='Test', first_seen_utc=datetime.now(timezone.utc).isoformat()),
                ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, impact_score=0.5, actionability_score=0.5, final_score=0.5),
                evidence=[],
                suggested_actions=[]
            )
            items.append(item)
            items_data.append({'id': f'msg{i}', 'title': f'Test {i}'})
        
        result = detector.detect_novelty_batch('user1', items, items_data)
        assert len(result) == 3
        assert all(item.novelty.label == 'NEW' for item in result)
        
    def test_get_novelty_stats(self):
        """Test getting novelty statistics"""
        detector = NoveltyDetector()
        
        items = []
        for i, label in enumerate(['NEW', 'NEW', 'REPEAT', 'UPDATED', 'NEW']):
            item = BriefItem(
                item_ref=f'item_{i}',
                source='gmail',
                type='email',
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                title=f'Test {i}',
                summary=f'Summary {i}',
                why_it_matters='Test',
                entities=[],
                novelty=NoveltyInfo(label=label, reason='Test', first_seen_utc=datetime.now(timezone.utc).isoformat()),
                ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, impact_score=0.5, actionability_score=0.5, final_score=0.5),
                evidence=[],
                suggested_actions=[]
            )
            items.append(item)
        
        stats = detector.get_novelty_stats(items)
        # Stats returns counts by label
        assert stats['NEW'] == 3
        assert stats['REPEAT'] == 1
        assert stats['UPDATED'] == 1


class TestMemoryManager:
    """Test MemoryManager"""
    
    def test_memory_manager_init(self, tmp_path):
        """Test memory manager initialization"""
        manager = MemoryManager(memory_dir=tmp_path)
        assert manager is not None
        assert manager.memory_dir.exists()
        
    def test_memory_manager_init_default(self):
        """Test memory manager with default directory"""
        manager = MemoryManager()
        assert manager is not None
        
    def test_has_seen(self, tmp_path):
        """Test checking if item has been seen"""
        manager = MemoryManager(memory_dir=tmp_path)
        
        fp = 'test_fingerprint'
        
        # Not seen yet
        assert not manager.has_seen('user1', fp)
        
        # Record it
        manager.record_item(
            user_id='user1',
            fingerprint=fp,
            content_hash='hash1',
            source='gmail',
            item_type='email',
            title='Test'
        )
        
        # Now it should be seen
        assert manager.has_seen('user1', fp)
        
    def test_get_item_memory(self, tmp_path):
        """Test getting item memory"""
        manager = MemoryManager(memory_dir=tmp_path)
        
        fp = 'test_fingerprint'
        
        # Not exists yet
        item_mem = manager.get_item_memory('user1', fp)
        assert item_mem is None
        
        # Record it
        manager.record_item(
            user_id='user1',
            fingerprint=fp,
            content_hash='hash1',
            source='gmail',
            item_type='email',
            title='Test Email'
        )
        
        # Now it should exist
        item_mem = manager.get_item_memory('user1', fp)
        assert item_mem is not None
        assert item_mem.fingerprint == fp
        assert item_mem.title == 'Test Email'
        
    def test_record_item_new(self, tmp_path):
        """Test recording new item"""
        manager = MemoryManager(memory_dir=tmp_path)
        
        item_mem = manager.record_item(
            user_id='user1',
            fingerprint='fp1',
            content_hash='hash1',
            source='gmail',
            item_type='email',
            title='Test'
        )
        
        assert item_mem.fingerprint == 'fp1'
        assert item_mem.seen_count == 1
        
    def test_record_item_update(self, tmp_path):
        """Test updating existing item"""
        manager = MemoryManager(memory_dir=tmp_path)
        
        # First time
        item_mem1 = manager.record_item(
            user_id='user1',
            fingerprint='fp1',
            content_hash='hash1',
            source='gmail',
            item_type='email'
        )
        
        # Second time
        item_mem2 = manager.record_item(
            user_id='user1',
            fingerprint='fp1',
            content_hash='hash1',
            source='gmail',
            item_type='email'
        )
        
        assert item_mem2.seen_count == 2
        
    def test_get_all_fingerprints(self, tmp_path):
        """Test getting all fingerprints"""
        manager = MemoryManager(memory_dir=tmp_path)
        
        # Record some items
        for i in range(3):
            manager.record_item(
                user_id='user1',
                fingerprint=f'fp_{i}',
                content_hash=f'hash_{i}',
                source='gmail',
                item_type='email'
            )
        
        fps = manager.get_all_fingerprints('user1')
        assert len(fps) == 3
        assert 'fp_0' in fps
        assert 'fp_1' in fps
        assert 'fp_2' in fps
        
    def test_get_memory_stats(self, tmp_path):
        """Test getting memory statistics"""
        manager = MemoryManager(memory_dir=tmp_path)
        
        # Record items from different sources
        manager.record_item('user1', 'fp1', 'hash1', 'gmail', 'email')
        manager.record_item('user1', 'fp2', 'hash2', 'gmail', 'email')
        manager.record_item('user1', 'fp3', 'hash3', 'calendar', 'event')
        
        stats = manager.get_memory_stats('user1')
        assert stats['total_items'] == 3
        assert 'gmail' in stats['by_source']
        assert 'calendar' in stats['by_source']
        
    def test_user_isolation(self, tmp_path):
        """Test that users are isolated"""
        manager = MemoryManager(memory_dir=tmp_path)
        
        manager.record_item('user1', 'fp1', 'hash1', 'gmail', 'email', 'User1 Email')
        manager.record_item('user2', 'fp1', 'hash1', 'gmail', 'email', 'User2 Email')
        
        item_mem1 = manager.get_item_memory('user1', 'fp1')
        item_mem2 = manager.get_item_memory('user2', 'fp1')
        
        assert item_mem1.title == 'User1 Email'
        assert item_mem2.title == 'User2 Email'
        
    def test_memory_persistence(self, tmp_path):
        """Test that memory persists across manager instances"""
        # First manager
        manager1 = MemoryManager(memory_dir=tmp_path)
        manager1.record_item('user1', 'fp1', 'hash1', 'gmail', 'email', 'Test')
        
        # Second manager (same directory)
        manager2 = MemoryManager(memory_dir=tmp_path)
        item_mem = manager2.get_item_memory('user1', 'fp1')
        
        # Should be able to retrieve the item
        assert item_mem is not None
        assert item_mem.fingerprint == 'fp1'

    def test_clear_memory(self, tmp_path):
        """Test clearing memory"""
        manager = MemoryManager(memory_dir=tmp_path)
        manager.record_item("u1", "fp1", "h1", "s1", "t1")
        manager.clear_memory("u1")
        assert not manager.has_seen("u1", "fp1")

    def test_prune_old_items(self, tmp_path):
        """Test pruning old items"""
        from packages.memory.memory_manager import ItemMemory
        manager = MemoryManager(memory_dir=tmp_path)
        # Record recent item
        manager.record_item("u1", "recent", "h1", "s1", "t1")
        
        # Record old item (manually manipulate memory file)
        memory = manager._load_memory("u1")
        memory["old"] = ItemMemory(
            fingerprint="old",
            content_hash="h2",
            first_seen_utc="2020-01-01T00:00:00+00:00",
            last_seen_utc="2020-01-01T00:00:00+00:00",
            seen_count=1,
            source="s1",
            item_type="t1"
        )
        manager._save_memory("u1", memory)
        
        pruned_count = manager.prune_old_items("u1", days_to_keep=30)
        assert pruned_count == 1
        assert not manager.has_seen("u1", "old")
        assert manager.has_seen("u1", "recent")

    def test_prune_empty_memory(self, tmp_path):
        """Test pruning empty memory returns 0"""
        manager = MemoryManager(memory_dir=tmp_path)
        assert manager.prune_old_items("nonexistent", days_to_keep=30) == 0

    def test_load_memory_error(self, tmp_path):
        """Test handling of corrupt memory file"""
        manager = MemoryManager(memory_dir=tmp_path)
        # Create a corrupt JSON file
        file_path = manager._get_user_file("corrupt_user")
        with open(file_path, 'w') as f:
            f.write("invalid json {")
        
        # Should catch exception and return empty dict
        memory = manager._load_memory("corrupt_user")
        assert memory == {}

    def test_save_memory_error(self, tmp_path):
        """Test handling of save memory error"""
        manager = MemoryManager(memory_dir=tmp_path)
        with patch('builtins.open', side_effect=IOError("Save failed")):
            # Should not raise
            manager._save_memory("u1", {})
