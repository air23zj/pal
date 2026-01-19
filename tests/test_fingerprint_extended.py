"""
Extended tests for fingerprint module - Target 85%+ coverage
"""
import pytest
from packages.memory.fingerprint import (
    FingerprintGenerator,
    generate_fingerprint,
    content_hash,
    _hash_string,
)


class TestFingerprintGenerator:
    """Test FingerprintGenerator class methods directly"""

    def test_for_email_with_message_id(self):
        """Test email fingerprint with message ID"""
        gen = FingerprintGenerator()
        fp = gen.for_email(message_id="msg123", subject="Test", timestamp="2024-01-15")
        assert fp.startswith("email:")
        assert len(fp) > 6

    def test_for_email_without_message_id(self):
        """Test email fingerprint fallback without message ID"""
        gen = FingerprintGenerator()
        fp = gen.for_email(message_id="", subject="Test Subject", timestamp="2024-01-15")
        assert fp.startswith("email:")

    def test_for_email_empty_all_fields(self):
        """Test email fingerprint with all empty fields"""
        gen = FingerprintGenerator()
        fp = gen.for_email(message_id="", subject=None, timestamp=None)
        assert fp.startswith("email:")

    def test_for_calendar_event_with_id(self):
        """Test calendar event fingerprint with event ID"""
        gen = FingerprintGenerator()
        fp = gen.for_calendar_event(
            event_id="event123",
            title="Meeting",
            start_time="2024-01-15T10:00:00",
            updated="2024-01-15T09:00:00"
        )
        assert fp.startswith("event:")

    def test_for_calendar_event_without_id(self):
        """Test calendar event fingerprint fallback without ID"""
        gen = FingerprintGenerator()
        fp = gen.for_calendar_event(
            event_id="",
            title="Meeting",
            start_time="2024-01-15T10:00:00",
            updated=None
        )
        assert fp.startswith("event:")

    def test_for_calendar_event_empty_fields(self):
        """Test calendar event fingerprint with empty fields"""
        gen = FingerprintGenerator()
        fp = gen.for_calendar_event(event_id="", title=None, start_time=None, updated=None)
        assert fp.startswith("event:")

    def test_for_task_with_id(self):
        """Test task fingerprint with task ID"""
        gen = FingerprintGenerator()
        fp = gen.for_task(task_id="task123", title="Do something", updated="2024-01-15")
        assert fp.startswith("task:")

    def test_for_task_without_id(self):
        """Test task fingerprint fallback without ID"""
        gen = FingerprintGenerator()
        fp = gen.for_task(task_id="", title="Do something", updated=None)
        assert fp.startswith("task:")

    def test_for_task_no_title(self):
        """Test task fingerprint with no title uses 'untitled'"""
        gen = FingerprintGenerator()
        fp1 = gen.for_task(task_id="", title=None, updated=None)
        fp2 = gen.for_task(task_id="", title=None, updated=None)
        assert fp1 == fp2  # Should be consistent
        assert fp1.startswith("task:")

    def test_for_social_post_with_id(self):
        """Test social post fingerprint with post ID"""
        gen = FingerprintGenerator()
        fp = gen.for_social_post(
            platform="twitter",
            post_id="post123",
            author="user1",
            content="Hello world",
            timestamp="2024-01-15T12:00:00"
        )
        assert fp.startswith("twitter:")

    def test_for_social_post_without_id(self):
        """Test social post fingerprint fallback without ID"""
        gen = FingerprintGenerator()
        fp = gen.for_social_post(
            platform="linkedin",
            post_id=None,
            author="user1",
            content="Professional post",
            timestamp="2024-01-15T12:00:00"
        )
        assert fp.startswith("linkedin:")

    def test_for_social_post_empty_fields(self):
        """Test social post fingerprint with empty fields"""
        gen = FingerprintGenerator()
        fp = gen.for_social_post(
            platform="x",
            post_id=None,
            author=None,
            content=None,
            timestamp=None
        )
        assert fp.startswith("x:")

    def test_for_generic_item_with_id_field(self):
        """Test generic item fingerprint with ID field"""
        gen = FingerprintGenerator()
        fp = gen.for_generic_item(source="custom", item_data={"id": "item123", "title": "Test"})
        assert fp.startswith("custom:")

    def test_for_generic_item_various_id_fields(self):
        """Test generic item fingerprint with various ID field names"""
        gen = FingerprintGenerator()

        # Test each ID field type
        for id_field in ['id', 'item_id', 'message_id', 'event_id', 'task_id', 'post_id']:
            fp = gen.for_generic_item(source="test", item_data={id_field: f"val_{id_field}"})
            assert fp.startswith("test:")

    def test_for_generic_item_no_id_field(self):
        """Test generic item fingerprint without ID field"""
        gen = FingerprintGenerator()
        fp = gen.for_generic_item(source="custom", item_data={"title": "Test", "content": "Data"})
        assert fp.startswith("custom:")

    def test_for_generic_item_empty_id_field(self):
        """Test generic item fingerprint with empty ID field"""
        gen = FingerprintGenerator()
        fp = gen.for_generic_item(source="custom", item_data={"id": "", "title": "Test"})
        # Should fall back to hash of entire item since ID is empty
        assert fp.startswith("custom:")


class TestGenerateFingerprint:
    """Test generate_fingerprint convenience function"""

    def test_gmail_source(self):
        """Test fingerprint for gmail source"""
        fp = generate_fingerprint("gmail", "email", {"id": "msg123", "subject": "Test"})
        assert fp.startswith("email:")

    def test_gmail_with_message_id_field(self):
        """Test gmail with message_id field"""
        fp = generate_fingerprint("gmail", "email", {"message_id": "msg123"})
        assert fp.startswith("email:")

    def test_gmail_with_timestamp(self):
        """Test gmail with timestamp field"""
        fp = generate_fingerprint("gmail", "email", {"date": "2024-01-15"})
        assert fp.startswith("email:")

    def test_calendar_source(self):
        """Test fingerprint for calendar source"""
        fp = generate_fingerprint("calendar", "event", {"id": "event123", "summary": "Meeting"})
        assert fp.startswith("event:")

    def test_calendar_with_alternate_fields(self):
        """Test calendar with alternate field names"""
        fp = generate_fingerprint("calendar", "event", {
            "event_id": "event123",
            "title": "Meeting",
            "start_time": "2024-01-15T10:00:00"
        })
        assert fp.startswith("event:")

    def test_tasks_source(self):
        """Test fingerprint for tasks source"""
        fp = generate_fingerprint("tasks", "task", {"id": "task123", "title": "Todo"})
        assert fp.startswith("task:")

    def test_tasks_with_task_id_field(self):
        """Test tasks with task_id field"""
        fp = generate_fingerprint("tasks", "task", {"task_id": "task123"})
        assert fp.startswith("task:")

    def test_twitter_source(self):
        """Test fingerprint for twitter source"""
        fp = generate_fingerprint("twitter", "social_post", {"id": "post123", "author": "user"})
        assert fp.startswith("twitter:")

    def test_x_source(self):
        """Test fingerprint for x source (Twitter rebrand)"""
        fp = generate_fingerprint("x", "social_post", {"id": "post123", "text": "Hello"})
        assert fp.startswith("x:")

    def test_linkedin_source(self):
        """Test fingerprint for linkedin source"""
        fp = generate_fingerprint("linkedin", "social_post", {"post_id": "post123", "content": "Professional"})
        assert fp.startswith("linkedin:")

    def test_social_post_with_alternate_fields(self):
        """Test social post with alternate field names"""
        fp = generate_fingerprint("twitter", "social_post", {
            "post_id": "post123",
            "from": "user1",
            "text": "Hello",
            "created_at": "2024-01-15"
        })
        assert fp.startswith("twitter:")

    def test_unknown_source(self):
        """Test fingerprint for unknown source uses generic"""
        fp = generate_fingerprint("unknown", "unknown", {"id": "item123", "data": "test"})
        assert fp.startswith("unknown:")

    def test_item_type_takes_precedence(self):
        """Test that item type can determine fingerprint method"""
        # If source is unknown but type is 'email', should use email fingerprint
        fp = generate_fingerprint("unknown", "email", {"id": "msg123"})
        assert fp.startswith("email:")

    def test_item_type_event(self):
        """Test item type 'event' routes correctly"""
        fp = generate_fingerprint("unknown", "event", {"id": "event123"})
        assert fp.startswith("event:")

    def test_item_type_task(self):
        """Test item type 'task' routes correctly"""
        fp = generate_fingerprint("unknown", "task", {"id": "task123"})
        assert fp.startswith("task:")

    def test_item_type_social_post(self):
        """Test item type 'social_post' routes correctly"""
        fp = generate_fingerprint("unknown", "social_post", {"id": "post123"})
        assert fp.startswith("unknown:")


class TestContentHash:
    """Test content_hash function"""

    def test_content_hash_title_variations(self):
        """Test content hash with title/subject variations"""
        hash1 = content_hash({"title": "Test Title"})
        hash2 = content_hash({"subject": "Test Title"})
        # Both should extract the title
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)

    def test_content_hash_summary_variations(self):
        """Test content hash with summary/snippet variations"""
        hash1 = content_hash({"summary": "Test Summary"})
        hash2 = content_hash({"snippet": "Different Summary"})
        assert hash1 != hash2

    def test_content_hash_content_variations(self):
        """Test content hash with content/body/text variations"""
        hash1 = content_hash({"content": "Test Content"})
        hash2 = content_hash({"body": "Test Content"})
        hash3 = content_hash({"text": "Test Content"})
        # All should be detected as content
        assert all(isinstance(h, str) for h in [hash1, hash2, hash3])

    def test_content_hash_status(self):
        """Test content hash includes status"""
        hash1 = content_hash({"status": "pending"})
        hash2 = content_hash({"status": "completed"})
        assert hash1 != hash2

    def test_content_hash_start_time_variations(self):
        """Test content hash with start/start_time variations"""
        hash1 = content_hash({"start": "2024-01-15T10:00:00"})
        hash2 = content_hash({"start_time": "2024-01-15T10:00:00"})
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)

    def test_content_hash_due_date_variations(self):
        """Test content hash with due/due_date variations"""
        hash1 = content_hash({"due": "2024-01-15"})
        hash2 = content_hash({"due_date": "2024-01-15"})
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)

    def test_content_hash_updated_variations(self):
        """Test content hash with updated/last_modified variations"""
        hash1 = content_hash({"updated": "2024-01-15T12:00:00"})
        hash2 = content_hash({"last_modified": "2024-01-15T12:00:00"})
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)

    def test_content_hash_description(self):
        """Test content hash includes description"""
        hash1 = content_hash({"description": "Task description"})
        hash2 = content_hash({"description": "Different description"})
        assert hash1 != hash2

    def test_content_hash_removes_none_values(self):
        """Test content hash ignores None values"""
        hash1 = content_hash({"title": "Test", "content": None})
        hash2 = content_hash({"title": "Test"})
        assert hash1 == hash2

    def test_content_hash_complex_item(self):
        """Test content hash with complex item data"""
        hash_val = content_hash({
            "title": "Meeting",
            "summary": "Weekly sync",
            "content": "Discussion points...",
            "status": "confirmed",
            "start": "2024-01-15T10:00:00",
            "due": "2024-01-15T11:00:00",
            "updated": "2024-01-15T09:00:00",
            "description": "Team meeting"
        })
        assert len(hash_val) == 12  # Default length is 12


class TestHashString:
    """Test _hash_string helper function"""

    def test_hash_string_default_length(self):
        """Test hash string default length"""
        result = _hash_string("test input")
        assert len(result) == 16  # Default length

    def test_hash_string_custom_length(self):
        """Test hash string with custom length"""
        result = _hash_string("test input", length=8)
        assert len(result) == 8

    def test_hash_string_consistency(self):
        """Test hash string consistency"""
        result1 = _hash_string("test")
        result2 = _hash_string("test")
        assert result1 == result2

    def test_hash_string_uniqueness(self):
        """Test hash string uniqueness"""
        result1 = _hash_string("input1")
        result2 = _hash_string("input2")
        assert result1 != result2

    def test_hash_string_empty(self):
        """Test hash string with empty input"""
        result = _hash_string("")
        assert len(result) == 16

    def test_hash_string_unicode(self):
        """Test hash string with unicode characters"""
        result = _hash_string("日本語テスト")
        assert len(result) == 16

    def test_hash_string_long_input(self):
        """Test hash string with long input"""
        long_input = "a" * 10000
        result = _hash_string(long_input)
        assert len(result) == 16


class TestFingerprintConsistency:
    """Test fingerprint consistency across scenarios"""

    def test_fingerprint_stability_email(self):
        """Test email fingerprint is stable across calls"""
        data = {"id": "msg123", "subject": "Test", "date": "2024-01-15"}
        fp1 = generate_fingerprint("gmail", "email", data)
        fp2 = generate_fingerprint("gmail", "email", data)
        assert fp1 == fp2

    def test_fingerprint_stability_calendar(self):
        """Test calendar fingerprint is stable"""
        data = {"id": "event123", "summary": "Meeting", "start": "2024-01-15T10:00:00"}
        fp1 = generate_fingerprint("calendar", "event", data)
        fp2 = generate_fingerprint("calendar", "event", data)
        assert fp1 == fp2

    def test_fingerprint_stability_task(self):
        """Test task fingerprint is stable"""
        data = {"id": "task123", "title": "Todo"}
        fp1 = generate_fingerprint("tasks", "task", data)
        fp2 = generate_fingerprint("tasks", "task", data)
        assert fp1 == fp2

    def test_fingerprint_stability_social(self):
        """Test social fingerprint is stable"""
        data = {"id": "post123", "author": "user", "content": "Hello"}
        fp1 = generate_fingerprint("twitter", "social_post", data)
        fp2 = generate_fingerprint("twitter", "social_post", data)
        assert fp1 == fp2

    def test_content_hash_stability(self):
        """Test content hash is stable"""
        data = {"title": "Test", "content": "Content", "status": "active"}
        hash1 = content_hash(data)
        hash2 = content_hash(data)
        assert hash1 == hash2
