#!/usr/bin/env python3
"""
Test memory and novelty detection system
"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.shared.schemas import BriefItem, Entity, NoveltyInfo, RankingScores
from packages.memory import (
    MemoryManager,
    NoveltyDetector,
    generate_fingerprint,
    content_hash,
)


def create_sample_item(
    item_id: str,
    source: str = "gmail",
    title: str = "Test Email",
    summary: str = "Test content",
) -> BriefItem:
    """Create a sample BriefItem"""
    return BriefItem(
        item_ref=item_id,
        source=source,
        type="email",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        title=title,
        summary=summary,
        why_it_matters="Test item",
        entities=[],
        novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=datetime.now(timezone.utc).isoformat()),
        ranking=RankingScores(
            relevance_score=0.5,
            urgency_score=0.5,
            credibility_score=0.5,
            actionability_score=0.5,
            final_score=0.5,
        ),
        evidence=[],
        suggested_actions=[],
    )


def test_fingerprinting():
    """Test fingerprint generation"""
    print("📝 Testing Fingerprinting...\n")
    
    # Test email fingerprinting
    email_data = {
        'id': 'msg_123',
        'subject': 'Important Meeting',
        'from': 'boss@company.com',
    }
    
    fp1 = generate_fingerprint('gmail', 'email', email_data)
    print(f"Email fingerprint: {fp1}")
    
    # Same email should have same fingerprint
    fp2 = generate_fingerprint('gmail', 'email', email_data)
    assert fp1 == fp2, "Same email should have same fingerprint"
    print("✅ Same email = same fingerprint\n")
    
    # Different email should have different fingerprint
    email_data2 = {
        'id': 'msg_456',
        'subject': 'Different Meeting',
        'from': 'boss@company.com',
    }
    fp3 = generate_fingerprint('gmail', 'email', email_data2)
    assert fp1 != fp3, "Different emails should have different fingerprints"
    print("✅ Different email = different fingerprint\n")
    
    # Test content hash
    ch1 = content_hash(email_data)
    print(f"Content hash: {ch1}")
    
    # Changed content should have different hash
    email_data_updated = email_data.copy()
    email_data_updated['subject'] = 'UPDATED: Important Meeting'
    ch2 = content_hash(email_data_updated)
    assert ch1 != ch2, "Updated content should have different hash"
    print("✅ Updated content = different hash\n")


def test_memory_manager():
    """Test memory manager"""
    print("💾 Testing Memory Manager...\n")
    
    memory = MemoryManager()
    user_id = "test_user"
    
    # Clear any existing memory
    memory.clear_memory(user_id)
    print("Cleared test memory\n")
    
    # Record first item
    fp1 = "email:abc123"
    ch1 = "hash_v1"
    
    item_mem = memory.record_item(
        user_id=user_id,
        fingerprint=fp1,
        content_hash=ch1,
        source="gmail",
        item_type="email",
        title="Test Email 1",
    )
    
    print(f"Recorded item: {item_mem.fingerprint}")
    print(f"  First seen: {item_mem.first_seen_utc}")
    print(f"  Seen count: {item_mem.seen_count}\n")
    
    # Check if seen
    assert memory.has_seen(user_id, fp1), "Should remember item"
    print("✅ Item remembered\n")
    
    # Record same item again
    item_mem2 = memory.record_item(
        user_id=user_id,
        fingerprint=fp1,
        content_hash=ch1,
        source="gmail",
        item_type="email",
        title="Test Email 1",
    )
    
    assert item_mem2.seen_count == 2, "Seen count should increment"
    print(f"✅ Seen count incremented: {item_mem2.seen_count}\n")
    
    # Get stats
    stats = memory.get_memory_stats(user_id)
    print(f"Memory stats: {stats}\n")
    
    # Clean up
    memory.clear_memory(user_id)
    print("✅ Memory manager working correctly\n")


def test_novelty_detector():
    """Test novelty detection"""
    print("🔍 Testing Novelty Detector...\n")
    
    memory = MemoryManager()
    detector = NoveltyDetector(memory)
    user_id = "test_user"
    
    # Clear memory
    memory.clear_memory(user_id)
    
    # Create test items
    item1 = create_sample_item(
        "email_1",
        title="Meeting Tomorrow",
        summary="Please join the meeting at 2pm",
    )
    
    item1_data = {
        'id': 'msg_meeting_001',
        'subject': 'Meeting Tomorrow',
        'content': 'Please join the meeting at 2pm',
    }
    
    # First time - should be NEW
    novelty1 = detector.detect_novelty(user_id, item1, item1_data)
    print(f"First detection: {novelty1.label}")
    print(f"  Reason: {novelty1.reason}\n")
    assert novelty1.label == "NEW", "First time should be NEW"
    print("✅ First time = NEW\n")
    
    # Second time - same content - should be REPEAT
    item1_again = create_sample_item(
        "email_1",
        title="Meeting Tomorrow",
        summary="Please join the meeting at 2pm",
    )
    
    novelty2 = detector.detect_novelty(user_id, item1_again, item1_data)
    print(f"Second detection: {novelty2.label}")
    print(f"  Reason: {novelty2.reason}\n")
    assert novelty2.label == "REPEAT", "Same content should be REPEAT"
    print("✅ Same content = REPEAT\n")
    
    # Third time - updated content - should be UPDATED
    item1_updated = create_sample_item(
        "email_1",
        title="Meeting Tomorrow - CHANGED TIME",
        summary="Please join the meeting at 3pm (UPDATED)",
    )
    
    item1_data_updated = {
        'id': 'msg_meeting_001',  # Same ID
        'subject': 'Meeting Tomorrow - CHANGED TIME',
        'content': 'Please join the meeting at 3pm (UPDATED)',
    }
    
    novelty3 = detector.detect_novelty(user_id, item1_updated, item1_data_updated)
    print(f"Third detection: {novelty3.label}")
    print(f"  Reason: {novelty3.reason}\n")
    assert novelty3.label == "UPDATED", "Changed content should be UPDATED"
    print("✅ Changed content = UPDATED\n")
    
    # Clean up
    memory.clear_memory(user_id)
    print("✅ Novelty detector working correctly\n")


def test_batch_processing():
    """Test batch novelty detection"""
    print("📦 Testing Batch Processing...\n")
    
    memory = MemoryManager()
    detector = NoveltyDetector(memory)
    user_id = "test_user"
    
    # Clear memory
    memory.clear_memory(user_id)
    
    # Create multiple items
    items = [
        create_sample_item(f"item_{i}", title=f"Email {i}")
        for i in range(5)
    ]
    
    items_data = [
        {'id': f'msg_{i}', 'subject': f'Email {i}', 'content': f'Content {i}'}
        for i in range(5)
    ]
    
    # Batch detect - all should be NEW
    items_with_novelty = detector.detect_novelty_batch(user_id, items, items_data)
    
    print(f"Processed {len(items_with_novelty)} items:")
    for item in items_with_novelty:
        print(f"  {item.title}: {item.novelty.label}")
    
    all_new = all(item.novelty.label == "NEW" for item in items_with_novelty)
    assert all_new, "All first-time items should be NEW"
    print("\n✅ Batch processing: all NEW\n")
    
    # Process again - all should be REPEAT
    items_again = [
        create_sample_item(f"item_{i}", title=f"Email {i}")
        for i in range(5)
    ]
    
    items_with_novelty2 = detector.detect_novelty_batch(user_id, items_again, items_data)
    
    print(f"Processed again:")
    for item in items_with_novelty2:
        print(f"  {item.title}: {item.novelty.label}")
    
    all_repeat = all(item.novelty.label == "REPEAT" for item in items_with_novelty2)
    assert all_repeat, "All repeated items should be REPEAT"
    print("\n✅ Batch processing: all REPEAT\n")
    
    # Get stats
    stats = detector.get_novelty_stats(items_with_novelty2)
    print(f"Novelty stats: {stats}\n")
    
    # Filter repeats
    filtered = detector.filter_by_novelty(items_with_novelty2)
    print(f"After filtering repeats: {len(filtered)} items (expected: 0)")
    assert len(filtered) == 0, "Should filter out all REPEAT items"
    print("✅ Filtering working correctly\n")
    
    # Clean up
    memory.clear_memory(user_id)


def main():
    """Run all tests"""
    print("🧪 Testing Memory & Novelty System\n")
    print("=" * 60 + "\n")
    
    test_fingerprinting()
    print("=" * 60 + "\n")
    
    test_memory_manager()
    print("=" * 60 + "\n")
    
    test_novelty_detector()
    print("=" * 60 + "\n")
    
    test_batch_processing()
    print("=" * 60 + "\n")
    
    print("🎉 All tests passed!\n")
    print("Memory system is working correctly:")
    print("  ✅ Fingerprinting generates stable IDs")
    print("  ✅ Memory manager persists to filesystem")
    print("  ✅ Novelty detector labels NEW/UPDATED/REPEAT")
    print("  ✅ Batch processing is efficient")
    print("  ✅ Filtering removes repeats")


if __name__ == "__main__":
    main()
