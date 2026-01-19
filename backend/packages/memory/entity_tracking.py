"""
Entity-Aware Update Detection

Tracks entities across items to detect meaningful updates:
- "New information about a known person/project/company"
- Timeline reconstruction for entities
- Context-aware update detection

Example:
    Item 1: "SpaceX announces Mars mission"
    Item 2: "SpaceX delays Mars mission to 2026"
    → Detected as UPDATE about entity "SpaceX"
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from packages.shared.schemas import BriefItem, Entity


@dataclass
class EntityState:
    """Tracks state of an entity over time"""

    entity_key: str
    entity_kind: str
    first_seen: datetime
    last_seen: datetime
    item_count: int
    recent_items: List[str]  # Fingerprints of recent items mentioning this entity
    attributes: Dict[str, any]  # Tracked attributes (status, dates, etc.)


@dataclass
class EntityUpdate:
    """Represents a detected update about an entity"""

    entity_key: str
    entity_kind: str
    update_type: str  # "new_info", "status_change", "date_change"
    old_value: Optional[any]
    new_value: Optional[any]
    description: str


@dataclass
class EntityUpdateResult:
    """Result of entity-aware update detection"""

    has_updates: bool
    entity_updates: List[EntityUpdate]
    new_entities: List[str]
    known_entities: List[str]
    summary: str


class EntityTracker:
    """
    Tracks entities across items to detect meaningful updates

    Storage:
    - In-memory state (can be persisted to database)
    - Per-user entity tracking
    - Attribute change detection
    """

    def __init__(self):
        """Initialize entity tracker"""
        # user_id -> entity_key -> EntityState
        self._entities: Dict[str, Dict[str, EntityState]] = defaultdict(dict)

    def _extract_entities(self, item: BriefItem) -> List[Entity]:
        """Extract entities from item"""
        return item.entities or []

    def _get_entity_key(self, entity: Entity) -> str:
        """Get unique key for entity"""
        return f"{entity.kind}:{entity.key}"

    def track_item(self, user_id: str, item: BriefItem, fingerprint: str) -> EntityUpdateResult:
        """
        Track entities in item and detect updates

        Args:
            user_id: User ID
            item: Item to track
            fingerprint: Item fingerprint

        Returns:
            EntityUpdateResult with detected updates
        """
        entities = self._extract_entities(item)
        if not entities:
            return EntityUpdateResult(
                has_updates=False,
                entity_updates=[],
                new_entities=[],
                known_entities=[],
                summary="No entities found",
            )

        user_entities = self._entities[user_id]
        new_entities = []
        known_entities = []
        entity_updates = []

        for entity in entities:
            entity_key = self._get_entity_key(entity)

            if entity_key not in user_entities:
                # New entity
                new_entities.append(entity_key)
                user_entities[entity_key] = EntityState(
                    entity_key=entity_key,
                    entity_kind=entity.kind,
                    first_seen=item.timestamp_utc,
                    last_seen=item.timestamp_utc,
                    item_count=1,
                    recent_items=[fingerprint],
                    attributes={},
                )
            else:
                # Known entity - check for updates
                known_entities.append(entity_key)
                state = user_entities[entity_key]

                # Detect attribute changes
                updates = self._detect_entity_updates(state, item, entity)
                entity_updates.extend(updates)

                # Update state
                state.last_seen = item.timestamp_utc
                state.item_count += 1
                state.recent_items.append(fingerprint)

                # Keep only last 10 items
                if len(state.recent_items) > 10:
                    state.recent_items = state.recent_items[-10:]

        # Generate summary
        has_updates = len(entity_updates) > 0
        if has_updates:
            summary = f"{len(entity_updates)} update(s) about {len(known_entities)} known entit(y|ies)"
        elif new_entities:
            summary = f"First mention of {len(new_entities)} new entit(y|ies)"
        else:
            summary = f"No updates about {len(known_entities)} known entit(y|ies)"

        return EntityUpdateResult(
            has_updates=has_updates,
            entity_updates=entity_updates,
            new_entities=new_entities,
            known_entities=known_entities,
            summary=summary,
        )

    def _detect_entity_updates(
        self, state: EntityState, item: BriefItem, entity: Entity
    ) -> List[EntityUpdate]:
        """
        Detect if item contains new information about entity

        Checks for:
        - Status changes (e.g., "planned" → "delayed")
        - Date changes (e.g., meeting time updated)
        - New attributes mentioned
        """
        updates = []

        # Check for status keywords in title/summary
        status_keywords = {
            "launch": "launched",
            "release": "released",
            "announce": "announced",
            "delay": "delayed",
            "cancel": "cancelled",
            "complete": "completed",
            "start": "started",
            "end": "ended",
        }

        text = f"{item.title} {item.summary}".lower()

        for keyword, status in status_keywords.items():
            if keyword in text:
                old_status = state.attributes.get("status")
                if old_status != status:
                    updates.append(
                        EntityUpdate(
                            entity_key=state.entity_key,
                            entity_kind=state.entity_kind,
                            update_type="status_change",
                            old_value=old_status,
                            new_value=status,
                            description=f"Status changed to '{status}'",
                        )
                    )
                    state.attributes["status"] = status
                    break  # Only one status per item

        # Check for date changes (for calendar events)
        if item.type == "calendar_event":
            # Extract date from item
            event_start = getattr(item, "start_time", None)
            if event_start:
                old_start = state.attributes.get("start_time")
                if old_start and old_start != event_start:
                    updates.append(
                        EntityUpdate(
                            entity_key=state.entity_key,
                            entity_kind=state.entity_kind,
                            update_type="date_change",
                            old_value=old_start,
                            new_value=event_start,
                            description=f"Start time changed from {old_start} to {event_start}",
                        )
                    )
                state.attributes["start_time"] = event_start

        # Detect "new information" by time gap
        days_since_last = (item.timestamp_utc - state.last_seen).days
        if days_since_last >= 7:  # New info after 7+ days
            updates.append(
                EntityUpdate(
                    entity_key=state.entity_key,
                    entity_kind=state.entity_kind,
                    update_type="new_info",
                    old_value=None,
                    new_value=None,
                    description=f"New information after {days_since_last} days",
                )
            )

        return updates

    def get_entity_timeline(self, user_id: str, entity_key: str) -> Optional[EntityState]:
        """
        Get timeline/history for an entity

        Args:
            user_id: User ID
            entity_key: Entity key (e.g., "person:alice@company.com")

        Returns:
            EntityState with history, or None if not tracked
        """
        return self._entities[user_id].get(entity_key)

    def get_all_entities(self, user_id: str) -> List[EntityState]:
        """Get all tracked entities for user"""
        return list(self._entities[user_id].values())

    def get_active_entities(
        self, user_id: str, days: int = 30
    ) -> List[EntityState]:
        """
        Get entities with activity in last N days

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of EntityState objects
        """
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
        active = []

        for state in self._entities[user_id].values():
            if state.last_seen.timestamp() >= cutoff:
                active.append(state)

        return sorted(active, key=lambda s: s.last_seen, reverse=True)

    def get_stats(self, user_id: str) -> Dict:
        """Get statistics about tracked entities"""
        entities = self._entities[user_id]

        # Count by kind
        by_kind = defaultdict(int)
        for state in entities.values():
            by_kind[state.entity_kind] += 1

        return {
            "total_entities": len(entities),
            "by_kind": dict(by_kind),
            "active_last_7d": len(self.get_active_entities(user_id, days=7)),
            "active_last_30d": len(self.get_active_entities(user_id, days=30)),
        }

    def clear_user_data(self, user_id: str):
        """Clear all entity data for user (for testing/cleanup)"""
        if user_id in self._entities:
            del self._entities[user_id]


# Singleton instance
_tracker_instance: Optional[EntityTracker] = None


def get_entity_tracker() -> EntityTracker:
    """Get or create singleton entity tracker"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = EntityTracker()
    return _tracker_instance
