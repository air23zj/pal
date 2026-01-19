"""
Memory consolidation service - learns user preferences from behavior.

This is the learning loop that makes Morning Brief smarter over time:
- Analyzes feedback events
- Updates topic weights automatically
- Promotes frequently-engaged people to VIP
- Learns which sources user trusts

Runs periodically (weekly) or on-demand.
"""
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from dataclasses import dataclass
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from packages.database.models import User, FeedbackEvent, Item
from packages.shared.schemas import Entity

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationResult:
    """Results from a consolidation run"""
    events_processed: int
    topics_updated: int
    topics_added: int
    vips_added: int
    sources_updated: int
    preferences_before: Dict[str, Any]
    preferences_after: Dict[str, Any]


class MemoryConsolidator:
    """
    Learns user preferences from feedback events.
    
    Implements three consolidation rules:
    1. Topic weight adjustment (engagement → topic weights)
    2. VIP auto-promotion (repeated engagement → VIP status)
    3. Source trust learning (engagement rate → source trust)
    """
    
    def __init__(self, db: Session):
        """
        Initialize consolidator.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def consolidate_user(
        self,
        user_id: str,
        since_date: Optional[datetime] = None,
        min_events: int = 5,
    ) -> Optional[ConsolidationResult]:
        """
        Run consolidation for one user.
        
        Args:
            user_id: User identifier
            since_date: Only process events since this date (default: last 7 days)
            min_events: Minimum events needed to run consolidation (default: 5)
            
        Returns:
            ConsolidationResult or None if not enough data
        """
        # Default to last 7 days
        if since_date is None:
            since_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Get feedback events
        events = self.db.scalars(
            select(FeedbackEvent)
            .where(FeedbackEvent.user_id == user_id)
            .where(FeedbackEvent.created_at_utc >= since_date)
            .order_by(FeedbackEvent.created_at_utc)
        ).all()
        
        if len(events) < min_events:
            logger.info(f"User {user_id}: Not enough events ({len(events)} < {min_events}), skipping consolidation")
            return None
        
        # Get user and current preferences
        user = self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            logger.error(f"User {user_id} not found")
            return None
        
        prefs = user.settings_json or {}
        prefs_before = prefs.copy()
        
        # Initialize preference structure if needed
        if 'topics' not in prefs:
            prefs['topics'] = {}
        if 'vip_people' not in prefs:
            prefs['vip_people'] = []
        if 'source_trust' not in prefs:
            prefs['source_trust'] = {}
        
        # Track changes
        initial_topic_count = len(prefs['topics'])
        initial_vip_count = len(prefs['vip_people'])
        initial_source_count = len(prefs['source_trust'])
        
        # Apply consolidation rules
        prefs = self._consolidate_topics(user_id, events, prefs)
        prefs = self._consolidate_vips(user_id, events, prefs)
        prefs = self._consolidate_source_trust(user_id, events, prefs)
        
        # Clean up preferences
        prefs = self._cleanup_preferences(prefs)
        
        # Save updated preferences
        user.settings_json = prefs
        self.db.commit()
        
        logger.info(
            f"User {user_id}: Consolidated {len(events)} events. "
            f"Topics: {len(prefs['topics'])} (+{len(prefs['topics']) - initial_topic_count}), "
            f"VIPs: {len(prefs['vip_people'])} (+{len(prefs['vip_people']) - initial_vip_count}), "
            f"Sources: {len(prefs['source_trust'])} (+{len(prefs['source_trust']) - initial_source_count})"
        )
        
        return ConsolidationResult(
            events_processed=len(events),
            topics_updated=len(prefs['topics']),
            topics_added=len(prefs['topics']) - initial_topic_count,
            vips_added=len(prefs['vip_people']) - initial_vip_count,
            sources_updated=len(prefs['source_trust']) - initial_source_count,
            preferences_before=prefs_before,
            preferences_after=prefs,
        )
    
    def _consolidate_topics(
        self,
        user_id: str,
        events: List[FeedbackEvent],
        prefs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Learn which topics matter to user from feedback.
        
        Rule: Engagement (save/open/thumb_up) increases topic weight,
              disengagement (dismiss/thumb_down) decreases it.
        
        Args:
            user_id: User identifier
            events: Feedback events to analyze
            prefs: Current preferences dict
            
        Returns:
            Updated preferences dict
        """
        topics = prefs.get('topics', {})
        
        # Positive signals
        positive_events = ['save', 'open', 'thumb_up']
        # Negative signals
        negative_events = ['dismiss', 'thumb_down', 'less_like_this']
        
        for event in events:
            # Get item to extract topics
            item = self.db.scalar(
                select(Item)
                .where(Item.user_id == user_id)
                .where(Item.id == event.item_id)
            )
            
            if not item:
                continue
            
            # Extract topics from item
            item_topics = self._extract_topics_from_item(item)
            
            for topic in item_topics:
                topic_lower = topic.lower()
                
                # Initialize topic if new
                if topic_lower not in topics:
                    topics[topic_lower] = 0.5  # Start at neutral
                
                # Adjust weight based on feedback type
                if event.event_type in positive_events:
                    topics[topic_lower] += 0.1  # Increase weight
                elif event.event_type in negative_events:
                    topics[topic_lower] -= 0.05  # Decrease weight (smaller to avoid over-penalizing)
                
                # Clamp to [0.0, 1.0]
                topics[topic_lower] = max(0.0, min(1.0, topics[topic_lower]))
        
        prefs['topics'] = topics
        return prefs
    
    def _consolidate_vips(
        self,
        user_id: str,
        events: List[FeedbackEvent],
        prefs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Promote frequently-engaged people to VIP status.
        
        Rule: If user engages with items from a person 3+ times,
              promote them to VIP.
        
        Args:
            user_id: User identifier
            events: Feedback events to analyze
            prefs: Current preferences dict
            
        Returns:
            Updated preferences dict
        """
        vip_people = set(prefs.get('vip_people', []))
        
        # Count engagement per person (only positive signals)
        positive_events = ['save', 'open', 'thumb_up']
        person_engagement = defaultdict(int)
        
        for event in events:
            if event.event_type not in positive_events:
                continue
            
            # Get item to extract people
            item = self.db.scalar(
                select(Item)
                .where(Item.user_id == user_id)
                .where(Item.id == event.item_id)
            )
            
            if not item:
                continue
            
            # Extract people from item
            people = self._extract_people_from_item(item)
            
            for person in people:
                person_lower = person.lower()
                person_engagement[person_lower] += 1
        
        # Promote to VIP if engaged 3+ times
        vip_threshold = 3
        for person, count in person_engagement.items():
            if count >= vip_threshold and person not in vip_people:
                vip_people.add(person)
                logger.info(f"User {user_id}: Promoted {person} to VIP (engaged {count} times)")
        
        prefs['vip_people'] = list(vip_people)
        return prefs
    
    def _consolidate_source_trust(
        self,
        user_id: str,
        events: List[FeedbackEvent],
        prefs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Learn which sources produce valuable content.
        
        Rule: Engagement rate per source determines trust level.
              Trust moves toward engagement rate (with smoothing).
        
        Args:
            user_id: User identifier
            events: Feedback events to analyze
            prefs: Current preferences dict
            
        Returns:
            Updated preferences dict
        """
        source_trust = prefs.get('source_trust', {})
        
        # Calculate engagement stats per source
        positive_events = ['save', 'open', 'thumb_up']
        source_stats = defaultdict(lambda: {'shown': 0, 'engaged': 0})
        
        # Track all items that generated events
        items_seen = set()
        
        for event in events:
            # Get item
            item = self.db.scalar(
                select(Item)
                .where(Item.user_id == user_id)
                .where(Item.id == event.item_id)
            )
            
            if not item:
                continue
            
            source = item.source
            
            # Count item once per source (avoid double-counting same item)
            item_key = f"{source}:{item.id}"
            if item_key not in items_seen:
                source_stats[source]['shown'] += 1
                items_seen.add(item_key)
            
            # Count engagement
            if event.event_type in positive_events:
                source_stats[source]['engaged'] += 1
        
        # Update trust based on engagement rate
        min_sample_size = 5  # Need at least 5 items to learn
        smoothing_factor = 0.3  # How much to adjust trust (0.3 = move 30% toward target)
        
        for source, stats in source_stats.items():
            if stats['shown'] < min_sample_size:
                continue  # Not enough data
            
            engagement_rate = stats['engaged'] / stats['shown']
            
            # Initialize if new source
            if source not in source_trust:
                source_trust[source] = 0.5  # Start at neutral
            
            # Move trust toward engagement rate (smoothed)
            current_trust = source_trust[source]
            new_trust = (1 - smoothing_factor) * current_trust + smoothing_factor * engagement_rate
            source_trust[source] = max(0.0, min(1.0, new_trust))
            
            logger.debug(
                f"User {user_id}: Source {source} trust: {current_trust:.2f} → {new_trust:.2f} "
                f"(engaged {stats['engaged']}/{stats['shown']} = {engagement_rate:.2%})"
            )
        
        prefs['source_trust'] = source_trust
        return prefs
    
    def _extract_topics_from_item(self, item: Item) -> List[str]:
        """
        Extract topics from an item.
        
        Topics come from:
        - Entity keys where kind='topic'
        - Keywords in title
        
        Args:
            item: Item to extract topics from
            
        Returns:
            List of topic strings
        """
        topics = []
        
        # Extract from entities
        if item.entity_keys_json:
            # entity_keys_json is a list of strings like ["topic:AI", "person:alice", ...]
            for entity_key in item.entity_keys_json:
                if entity_key.startswith('topic:'):
                    topic = entity_key.replace('topic:', '')
                    topics.append(topic)
        
        # Extract keywords from title (simple approach)
        if item.title:
            # Extract meaningful words (3+ chars, lowercase)
            words = [w.lower() for w in item.title.split() if len(w) >= 3]
            # Filter common words
            stopwords = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'has', 'was', 'are'}
            keywords = [w for w in words if w not in stopwords]
            topics.extend(keywords[:3])  # Take top 3 keywords
        
        return topics
    
    def _extract_people_from_item(self, item: Item) -> List[str]:
        """
        Extract people from an item.
        
        People come from:
        - Entity keys where kind='person'
        - Email 'from' field
        - Event attendees
        
        Args:
            item: Item to extract people from
            
        Returns:
            List of person identifiers (emails, names)
        """
        people = []
        
        # Extract from entities
        if item.entity_keys_json:
            for entity_key in item.entity_keys_json:
                if entity_key.startswith('person:'):
                    person = entity_key.replace('person:', '')
                    people.append(person)
        
        # Extract from summary for emails
        if item.type == 'email' and item.summary:
            # Look for "From: email@domain.com" pattern
            import re
            email_pattern = r'From:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            matches = re.findall(email_pattern, item.summary)
            people.extend(matches)
        
        return people
    
    def _cleanup_preferences(self, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up preferences to remove noise.
        
        - Remove topics with weight < 0.1 (too low, probably noise)
        - Remove duplicate VIPs
        - Remove sources with trust < 0.1
        
        Args:
            prefs: Preferences dict
            
        Returns:
            Cleaned preferences dict
        """
        # Remove low-weight topics
        if 'topics' in prefs:
            prefs['topics'] = {
                topic: weight
                for topic, weight in prefs['topics'].items()
                if weight >= 0.1
            }
        
        # Remove duplicate VIPs (case-insensitive)
        if 'vip_people' in prefs:
            seen = set()
            unique_vips = []
            for vip in prefs['vip_people']:
                vip_lower = vip.lower()
                if vip_lower not in seen:
                    seen.add(vip_lower)
                    unique_vips.append(vip)
            prefs['vip_people'] = unique_vips
        
        # Remove low-trust sources
        if 'source_trust' in prefs:
            prefs['source_trust'] = {
                source: trust
                for source, trust in prefs['source_trust'].items()
                if trust >= 0.1
            }
        
        return prefs
    
    def consolidate_all_users(
        self,
        since_date: Optional[datetime] = None,
        min_events: int = 5,
    ) -> Dict[str, ConsolidationResult]:
        """
        Run consolidation for all users.
        
        Args:
            since_date: Only process events since this date (default: last 7 days)
            min_events: Minimum events needed per user
            
        Returns:
            Dict mapping user_id to ConsolidationResult
        """
        users = self.db.scalars(select(User)).all()
        
        results = {}
        for user in users:
            try:
                result = self.consolidate_user(
                    user_id=user.id,
                    since_date=since_date,
                    min_events=min_events,
                )
                if result:
                    results[user.id] = result
            except Exception as e:
                logger.error(f"Error consolidating user {user.id}: {e}", exc_info=True)
        
        logger.info(f"Consolidated {len(results)} users")
        return results
    
    def get_consolidation_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of learned preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Summary dict with top topics, VIPs, trusted sources
        """
        user = self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            return {}
        
        prefs = user.settings_json or {}
        
        # Get top topics (sorted by weight)
        topics = prefs.get('topics', {})
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get VIPs
        vips = prefs.get('vip_people', [])
        
        # Get trusted sources (sorted by trust)
        sources = prefs.get('source_trust', {})
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'user_id': user_id,
            'top_topics': [{'topic': t, 'weight': w} for t, w in top_topics],
            'vip_people': vips,
            'trusted_sources': [{'source': s, 'trust': t} for s, t in top_sources],
            'total_topics': len(topics),
            'total_vips': len(vips),
            'total_sources': len(sources),
        }
