"""
Data Normalization Pipeline
Converts connector results into BriefItem format
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import hashlib
import logging

from packages.shared.schemas import (
    BriefItem,
    Entity,
    NoveltyInfo,
    RankingScores,
    Evidence,
    SuggestedAction,
)
from packages.connectors.base import ConnectorResult

logger = logging.getLogger(__name__)


class Normalizer:
    """
    Normalizes data from various sources into BriefItem format.
    Extracts entities, creates stable IDs, and prepares for ranking.
    """
    
    @staticmethod
    def generate_stable_id(source: str, type: str, source_id: str) -> str:
        """
        Generate stable hash ID for an item.
        
        Args:
            source: Source name (gmail, calendar, tasks, etc.)
            type: Item type (email, event, task, etc.)
            source_id: Source-specific ID
            
        Returns:
            Stable hash ID
        """
        key = f"{source}:{type}:{source_id}"
        return f"item_{source}_{hashlib.sha256(key.encode()).hexdigest()[:12]}"
    
    @staticmethod
    def extract_entities(item_data: Dict[str, Any], source: str) -> List[Entity]:
        """
        Extract entities from item data.
        
        Args:
            item_data: Raw item data from connector
            source: Source name
            
        Returns:
            List of entities
        """
        entities = []
        
        # Extract based on source type
        if source == "gmail":
            # Extract from sender
            from_addr = item_data.get('from', '')
            if from_addr:
                entities.append(Entity(kind="person", key=from_addr))
            
            # TODO: Extract topics from subject/body using NLP
            
        elif source == "calendar":
            # Extract attendees as entities
            for attendee in item_data.get('attendees', []):
                if attendee.get('email'):
                    entities.append(Entity(kind="person", key=attendee['email']))
            
            # Extract organizer
            organizer = item_data.get('organizer')
            if organizer:
                entities.append(Entity(kind="person", key=organizer))
        
        elif source == "tasks":
            # Extract from list name
            list_name = item_data.get('list_name', '')
            if list_name:
                entities.append(Entity(kind="project", key=list_name.lower().replace(' ', '_')))
        
        return entities
    
    @staticmethod
    def create_novelty_info() -> NoveltyInfo:
        """
        Create novelty info.
        Actual novelty detection will be done by the memory system.
        For now, mark everything as NEW.
        """
        return NoveltyInfo(
            label="NEW",
            reason="First time seen (novelty detection pending)",
            first_seen_utc=datetime.now(timezone.utc).isoformat(),
        )
    
    @staticmethod
    def create_initial_ranking() -> RankingScores:
        """
        Create initial ranking scores.
        Actual ranking will be computed by the ranking system.
        For now, use default scores.
        """
        return RankingScores(
            relevance_score=0.5,
            urgency_score=0.5,
            credibility_score=0.8,  # MCP sources are credible
            impact_score=0.5,
            actionability_score=0.5,
            final_score=0.5,
        )
    
    @staticmethod
    def create_evidence(item_data: Dict[str, Any], source: str) -> List[Evidence]:
        """
        Create evidence list for item.
        
        Args:
            item_data: Raw item data
            source: Source name
            
        Returns:
            List of evidence
        """
        evidence = []
        
        # Add URL if available
        url = item_data.get('url')
        if url:
            evidence.append(Evidence(
                kind="url",
                title=f"Open in {source.title()}",
                url=url,
            ))
        
        return evidence
    
    @staticmethod
    def create_suggested_actions(item_data: Dict[str, Any], source: str, type: str) -> List[SuggestedAction]:
        """
        Create suggested actions based on item type.
        
        Args:
            item_data: Raw item data
            source: Source name
            type: Item type
            
        Returns:
            List of suggested actions
        """
        actions = []
        
        if type == "email":
            actions.append(SuggestedAction(type="reply", label="Reply to email"))
            if item_data.get('is_unread'):
                actions.append(SuggestedAction(type="mark_read", label="Mark as read"))
        
        elif type == "event":
            actions.append(SuggestedAction(type="view_details", label="View event details"))
            if item_data.get('meeting_link'):
                actions.append(SuggestedAction(type="join_meeting", label="Join meeting"))
        
        elif type == "task":
            if not item_data.get('is_completed'):
                actions.append(SuggestedAction(type="complete_task", label="Mark as complete"))
            actions.append(SuggestedAction(type="view_task", label="View in Tasks"))
        
        # Always offer bookmark action
        actions.append(SuggestedAction(type="bookmark", label="Save for later"))
        
        return actions
    
    @staticmethod
    def normalize_gmail_item(item_data: Dict[str, Any]) -> BriefItem:
        """Normalize Gmail item to BriefItem"""
        source = "gmail"
        type = "email"
        source_id = item_data['source_id']
        
        # Generate stable ID
        item_ref = Normalizer.generate_stable_id(source, type, source_id)
        
        # Create brief summary
        summary = item_data.get('snippet', '')[:200]
        
        # Determine title
        subject = item_data.get('subject', '(No subject)')
        from_addr = item_data.get('from', 'Unknown')
        title = f"{subject} - from {from_addr}"
        
        return BriefItem(
            item_ref=item_ref,
            source=source,
            type=type,
            timestamp_utc=item_data['timestamp_utc'],
            source_id=source_id,
            url=item_data.get('url'),
            title=title,
            summary=summary,
            why_it_matters="New email (importance scoring pending)",
            entities=Normalizer.extract_entities(item_data, source),
            novelty=Normalizer.create_novelty_info(),
            ranking=Normalizer.create_initial_ranking(),
            evidence=Normalizer.create_evidence(item_data, source),
            suggested_actions=Normalizer.create_suggested_actions(item_data, source, type),
        )
    
    @staticmethod
    def normalize_calendar_item(item_data: Dict[str, Any]) -> BriefItem:
        """Normalize Calendar item to BriefItem"""
        source = "calendar"
        type = "event"
        source_id = item_data['source_id']
        
        # Generate stable ID
        item_ref = Normalizer.generate_stable_id(source, type, source_id)
        
        # Create summary
        start_time = datetime.fromisoformat(item_data['start_time'].replace('Z', '+00:00'))
        time_str = start_time.strftime("%I:%M %p")
        location = item_data.get('location', '')
        summary = f"Starts at {time_str}"
        if location:
            summary += f" at {location}"
        if item_data.get('attendee_count', 0) > 0:
            summary += f" with {item_data['attendee_count']} attendees"
        
        return BriefItem(
            item_ref=item_ref,
            source=source,
            type=type,
            timestamp_utc=item_data['timestamp_utc'],
            source_id=source_id,
            url=item_data.get('url'),
            title=item_data['title'],
            summary=summary,
            why_it_matters="Upcoming event (importance scoring pending)",
            entities=Normalizer.extract_entities(item_data, source),
            novelty=Normalizer.create_novelty_info(),
            ranking=Normalizer.create_initial_ranking(),
            evidence=Normalizer.create_evidence(item_data, source),
            suggested_actions=Normalizer.create_suggested_actions(item_data, source, type),
        )
    
    @staticmethod
    def normalize_task_item(item_data: Dict[str, Any]) -> BriefItem:
        """Normalize Task item to BriefItem"""
        source = "tasks"
        type = "task"
        source_id = item_data['source_id']
        
        # Generate stable ID
        item_ref = Normalizer.generate_stable_id(source, type, source_id)
        
        # Create summary
        summary = f"List: {item_data.get('list_name', 'Unknown')}"
        if item_data.get('due_date'):
            summary += f" | Due: {item_data['due_date']}"
            if item_data.get('is_overdue'):
                summary += " (OVERDUE)"
            elif item_data.get('is_due_today'):
                summary += " (TODAY)"
        
        return BriefItem(
            item_ref=item_ref,
            source=source,
            type=type,
            timestamp_utc=item_data['timestamp_utc'],
            source_id=source_id,
            url=item_data.get('url'),
            title=item_data['title'],
            summary=summary,
            why_it_matters="Pending task (importance scoring pending)",
            entities=Normalizer.extract_entities(item_data, source),
            novelty=Normalizer.create_novelty_info(),
            ranking=Normalizer.create_initial_ranking(),
            evidence=Normalizer.create_evidence(item_data, source),
            suggested_actions=Normalizer.create_suggested_actions(item_data, source, type),
        )

    @staticmethod
    def normalize_keep_item(item_data: Dict[str, Any]) -> BriefItem:
        """Normalize Google Keep note to BriefItem"""
        source = "keep"
        type = "note"
        source_id = item_data['source_id']

        # Generate stable ID
        item_ref = Normalizer.generate_stable_id(source, type, source_id)

        # Create summary based on note type
        note_type = item_data.get('note_type', 'text')
        summary_parts = [f"Type: {note_type}"]

        if item_data.get('labels'):
            summary_parts.append(f"Labels: {', '.join(item_data['labels'][:3])}")

        if item_data.get('is_pinned'):
            summary_parts.append("📌 Pinned")

        if item_data.get('is_urgent'):
            summary_parts.append("🚨 Urgent")

        summary = " | ".join(summary_parts)

        # Handle checklist items
        if note_type == "list" and item_data.get('checklist_items'):
            total_items = len(item_data['checklist_items'])
            checked_items = sum(1 for item in item_data['checklist_items'] if item.get('is_checked', False))
            summary += f" | Checklist: {checked_items}/{total_items} completed"

        # Handle attachments
        if item_data.get('has_attachments'):
            attachment_count = len(item_data.get('attachments', []))
            summary += f" | {attachment_count} attachment{'s' if attachment_count != 1 else ''}"

        return BriefItem(
            item_ref=item_ref,
            source=source,
            type=type,
            timestamp_utc=item_data['timestamp_utc'],
            source_id=source_id,
            url=item_data.get('url'),
            title=item_data['title'],
            summary=summary,
            why_it_matters="Personal note/reminder (importance scoring pending)",
            entities=Normalizer.extract_entities(item_data, source),
            novelty=Normalizer.create_novelty_info(),
            ranking=Normalizer.create_initial_ranking(),
            evidence=Normalizer.create_evidence(item_data, source),
            suggested_actions=Normalizer.create_suggested_actions(item_data, source, type),
        )

    @staticmethod
    def normalize_social_post(item_data: Dict[str, Any], source: str) -> BriefItem:
        """
        Normalize social media post to BriefItem.
        
        Works for Twitter/X, LinkedIn, and other social platforms.
        
        Args:
            item_data: Post data dict with keys:
                - id: Post ID
                - author: Author handle/name
                - content: Post text
                - timestamp: Post timestamp (ISO format)
                - url: Post URL (optional)
                - metrics: Engagement metrics dict (optional)
            source: Source platform (twitter, x, linkedin, etc.)
        
        Returns:
            Normalized BriefItem
        """
        type = "social_post"
        source_id = item_data['id']
        
        # Generate stable ID
        item_ref = Normalizer.generate_stable_id(source, type, source_id)
        
        # Format title (first line or truncated content)
        content = item_data.get('content', '')
        title_lines = content.split('\n')
        title = title_lines[0] if title_lines else content
        if len(title) > 80:
            title = title[:77] + "..."
        
        # Add author to title
        author = item_data.get('author', 'Unknown')
        title = f"{author}: {title}"
        
        # Create summary with engagement metrics
        metrics = item_data.get('metrics', {})
        summary_parts = []
        
        if source in ['twitter', 'x']:
            # Twitter metrics
            if metrics.get('likes', 0) > 0:
                summary_parts.append(f"{metrics['likes']} likes")
            if metrics.get('retweets', 0) > 0:
                summary_parts.append(f"{metrics['retweets']} retweets")
            if metrics.get('replies', 0) > 0:
                summary_parts.append(f"{metrics['replies']} replies")
        elif source == 'linkedin':
            # LinkedIn metrics
            if metrics.get('reactions', 0) > 0:
                summary_parts.append(f"{metrics['reactions']} reactions")
            if metrics.get('comments', 0) > 0:
                summary_parts.append(f"{metrics['comments']} comments")
            if metrics.get('shares', 0) > 0:
                summary_parts.append(f"{metrics['shares']} shares")
        
        summary = " | ".join(summary_parts) if summary_parts else "No engagement yet"
        
        # Add content preview to summary
        if len(content) > 200:
            summary = f"{content[:200]}... | {summary}"
        else:
            summary = f"{content} | {summary}"
        
        # Extract timestamp
        timestamp_utc = item_data.get('timestamp')
        if timestamp_utc and isinstance(timestamp_utc, str):
            # Already ISO format
            pass
        elif timestamp_utc:
            timestamp_utc = timestamp_utc.isoformat()
        else:
            timestamp_utc = datetime.now(timezone.utc).isoformat()
        
        # Create entities (author as person entity)
        entities = []
        if author and author != 'Unknown':
            entities.append(Entity(kind="person", key=author))
        
        # Add evidence with post URL
        evidence = []
        post_url = item_data.get('url')
        if post_url:
            evidence.append(Evidence(
                kind="url",
                title=f"{source.title()} post",
                url=post_url
            ))
        
        # Suggested actions
        suggested_actions = []
        if post_url:
            suggested_actions.append(SuggestedAction(
                type="open_link",
                label=f"View on {source.title()}",
                payload={"url": post_url}
            ))
        
        return BriefItem(
            item_ref=item_ref,
            source=source,
            type=type,
            timestamp_utc=timestamp_utc,
            source_id=source_id,
            url=item_data.get('url'),
            title=title,
            summary=summary,
            why_it_matters="Social post (importance scoring pending)",
            entities=entities,
            novelty=Normalizer.create_novelty_info(),
            ranking=Normalizer.create_initial_ranking(),
            evidence=evidence,
            suggested_actions=suggested_actions,
        )


def normalize_connector_result(result: ConnectorResult) -> List[BriefItem]:
    """
    Normalize a ConnectorResult into a list of BriefItems.

    Args:
        result: ConnectorResult from a connector

    Returns:
        List of normalized BriefItems
    """
    brief_items = []

    for item_data in result.items:
        try:
            if result.source == "gmail":
                brief_item = Normalizer.normalize_gmail_item(item_data)
            elif result.source == "calendar":
                brief_item = Normalizer.normalize_calendar_item(item_data)
            elif result.source == "tasks":
                brief_item = Normalizer.normalize_task_item(item_data)
            elif result.source == "keep":
                brief_item = Normalizer.normalize_keep_item(item_data)
            elif result.source in ["twitter", "x", "linkedin"]:
                brief_item = Normalizer.normalize_social_post(item_data, result.source)
            else:
                logger.warning(f"Unknown source: {result.source}")
                continue

            brief_items.append(brief_item)
        except Exception as e:
            logger.error(f"Error normalizing item from {result.source}: {e}", exc_info=True)
            continue

    return brief_items


def normalize_social_posts(posts: List[Dict[str, Any]], source: str) -> List[BriefItem]:
    """
    Convenience function to normalize social media posts.

    Args:
        posts: List of post dicts from social media agent
        source: Source platform (twitter, x, linkedin)

    Returns:
        List of normalized BriefItems
    """
    brief_items = []

    for post in posts:
        try:
            brief_item = Normalizer.normalize_social_post(post, source)
            brief_items.append(brief_item)
        except Exception as e:
            logger.error(f"Error normalizing social post from {source}: {e}", exc_info=True)
            continue

    return brief_items
