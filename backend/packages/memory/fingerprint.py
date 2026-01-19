"""
Item fingerprinting for duplicate detection and novelty tracking.

Fingerprints are stable IDs that identify "the same thing" across fetches.
"""
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime


class FingerprintGenerator:
    """
    Generates stable fingerprints for items from different sources.
    
    A fingerprint should:
    - Be stable across fetches (same item = same fingerprint)
    - Change when content meaningfully changes
    - Be unique per item
    """
    
    @staticmethod
    def for_email(
        message_id: str,
        subject: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> str:
        """
        Generate fingerprint for email.
        
        Args:
            message_id: Email message ID (primary key)
            subject: Email subject (for content hash)
            timestamp: Email timestamp
            
        Returns:
            Stable fingerprint string
        """
        # Primary: message_id is stable
        if message_id:
            return f"email:{_hash_string(message_id)}"
        
        # Fallback: subject + timestamp
        parts = [subject or "", timestamp or ""]
        content = "|".join(parts)
        return f"email:{_hash_string(content)}"
    
    @staticmethod
    def for_calendar_event(
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        updated: Optional[str] = None,
    ) -> str:
        """
        Generate fingerprint for calendar event.
        
        Args:
            event_id: Calendar event ID
            title: Event title
            start_time: Event start time
            updated: Last updated timestamp
            
        Returns:
            Stable fingerprint string
        """
        # Primary: event_id
        if event_id:
            return f"event:{_hash_string(event_id)}"
        
        # Fallback: title + start_time
        parts = [title or "", start_time or ""]
        content = "|".join(parts)
        return f"event:{_hash_string(content)}"
    
    @staticmethod
    def for_task(
        task_id: str,
        title: Optional[str] = None,
        updated: Optional[str] = None,
    ) -> str:
        """
        Generate fingerprint for task.
        
        Args:
            task_id: Task ID
            title: Task title
            updated: Last updated timestamp
            
        Returns:
            Stable fingerprint string
        """
        # Primary: task_id
        if task_id:
            return f"task:{_hash_string(task_id)}"
        
        # Fallback: title
        return f"task:{_hash_string(title or 'untitled')}"
    
    @staticmethod
    def for_social_post(
        platform: str,
        post_id: Optional[str] = None,
        author: Optional[str] = None,
        content: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> str:
        """
        Generate fingerprint for social media post.
        
        Args:
            platform: Platform name (twitter, linkedin, etc.)
            post_id: Post ID (if available)
            author: Post author
            content: Post content
            timestamp: Post timestamp
            
        Returns:
            Stable fingerprint string
        """
        # Primary: post_id
        if post_id:
            return f"{platform}:{_hash_string(post_id)}"
        
        # Fallback: author + content + timestamp
        parts = [author or "", content or "", timestamp or ""]
        content_str = "|".join(parts)
        return f"{platform}:{_hash_string(content_str)}"
    
    @staticmethod
    def for_generic_item(
        source: str,
        item_data: Dict[str, Any],
    ) -> str:
        """
        Generate fingerprint for generic item.
        
        Args:
            source: Source identifier
            item_data: Item data dict
            
        Returns:
            Stable fingerprint string
        """
        # Try common ID fields
        for id_field in ['id', 'item_id', 'message_id', 'event_id', 'task_id', 'post_id']:
            if id_field in item_data and item_data[id_field]:
                return f"{source}:{_hash_string(str(item_data[id_field]))}"
        
        # Fallback: hash entire item
        item_json = json.dumps(item_data, sort_keys=True)
        return f"{source}:{_hash_string(item_json)}"


def _hash_string(s: str, length: int = 16) -> str:
    """
    Hash a string to a short hex digest.
    
    Args:
        s: String to hash
        length: Length of output hex string (default: 16 chars)
        
    Returns:
        Hex digest of specified length
    """
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:length]


def generate_fingerprint(
    source: str,
    item_type: str,
    item_data: Dict[str, Any],
) -> str:
    """
    Convenience function to generate fingerprint for any item.
    
    Args:
        source: Source identifier (gmail, calendar, tasks, etc.)
        item_type: Item type (email, event, task, etc.)
        item_data: Item data dict
        
    Returns:
        Stable fingerprint string
    """
    gen = FingerprintGenerator()
    
    # Route to specific fingerprint method
    if source == "gmail" or item_type == "email":
        return gen.for_email(
            message_id=item_data.get('id') or item_data.get('message_id', ''),
            subject=item_data.get('subject') or item_data.get('title'),
            timestamp=item_data.get('timestamp') or item_data.get('date'),
        )
    
    elif source == "calendar" or item_type == "event":
        return gen.for_calendar_event(
            event_id=item_data.get('id') or item_data.get('event_id', ''),
            title=item_data.get('title') or item_data.get('summary'),
            start_time=item_data.get('start') or item_data.get('start_time'),
            updated=item_data.get('updated'),
        )
    
    elif source == "tasks" or item_type == "task":
        return gen.for_task(
            task_id=item_data.get('id') or item_data.get('task_id', ''),
            title=item_data.get('title'),
            updated=item_data.get('updated'),
        )
    
    elif source in ["twitter", "x", "linkedin"] or item_type == "social_post":
        return gen.for_social_post(
            platform=source,
            post_id=item_data.get('id') or item_data.get('post_id'),
            author=item_data.get('author') or item_data.get('from'),
            content=item_data.get('content') or item_data.get('text'),
            timestamp=item_data.get('timestamp') or item_data.get('created_at'),
        )
    
    else:
        # Generic fallback
        return gen.for_generic_item(source, item_data)


def content_hash(item_data: Dict[str, Any]) -> str:
    """
    Generate a content hash for detecting updates.
    
    This is different from fingerprint - fingerprint identifies the item,
    content hash detects if it changed.
    
    Args:
        item_data: Item data dict
        
    Returns:
        Content hash string
    """
    # Extract mutable fields that indicate updates
    # Try multiple field names for flexibility
    relevant_fields = {
        'title': item_data.get('title') or item_data.get('subject'),
        'summary': item_data.get('summary') or item_data.get('snippet'),
        'content': item_data.get('content') or item_data.get('body') or item_data.get('text'),
        'status': item_data.get('status'),
        'start': item_data.get('start') or item_data.get('start_time'),
        'due': item_data.get('due') or item_data.get('due_date'),
        'updated': item_data.get('updated') or item_data.get('last_modified'),
        'description': item_data.get('description'),
    }
    
    # Remove None values
    relevant_fields = {k: v for k, v in relevant_fields.items() if v is not None}
    
    # Hash
    content_json = json.dumps(relevant_fields, sort_keys=True)
    return _hash_string(content_json, length=12)
