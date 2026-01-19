# Morning Brief Memory System - Simplified & Practical

**Purpose:** A clear, actionable guide to building Morning Brief's memory system  
**Audience:** Software engineers implementing the system  
**Status:** Aligned with current MVP implementation

> **Related:** See [memory.md](./memory.md) for the brain-inspired conceptual design

---

## 1. The Core Problems

Morning Brief needs to solve these memory challenges:

**Problem A: Duplicate Detection**  
No one wants to see the same email/post/paper multiple times across daily briefs.

**Problem B: Meaningful Updates**  
A meeting time change at 3 PM is important. A typo fix in the agenda is not. How do we tell the difference?

**Problem C: Personalization**  
What's important varies wildly per person. One person cares about AI research papers, another about family logistics.

**Problem D: Explainability**  
Users need to trust the system. Why was this item shown? Why was that one filtered out?

---

## 2. The Key Insight (Our Moat)

**Memory-driven personalization through consolidation:**

```
What you see → What you do → What we learn → What you'll see next
    ↓              ↓              ↓                    ↓
  Items        Feedback     Topic weights        Better ranking
               (clicks,     VIP people           Fewer misses
                saves,      Source trust)        Less noise
                dismisses)
```

**This is the moat:** Most aggregators just show everything or use static rules. We **learn from your behavior** and get better over time.

The technical term: **episodic-to-semantic consolidation** (short-term observations → long-term preferences)

---

## 3. Memory Architecture (Simple 3-Layer)

### Layer 1: Item Tracking (Anti-Duplicate)

**Purpose:** Never show the same thing twice

**Implementation:**
- Filesystem storage: `memory_store/{user_id}_memory.json`
- One record per seen item
- Fast lookup by fingerprint

**Data Structure:**
```json
{
  "email:abc123": {
    "fingerprint": "email:abc123",
    "content_hash": "xyz789",
    "first_seen_utc": "2026-01-15T08:00:00Z",
    "last_seen_utc": "2026-01-19T08:00:00Z",
    "seen_count": 3,
    "source": "gmail",
    "item_type": "email",
    "title": "Q4 Planning Meeting"
  }
}
```

**Key Operations:**
- `has_seen(fingerprint)` → boolean
- `record_item(fingerprint, content_hash, ...)` → update or create
- `detect_update(fingerprint, new_content_hash)` → boolean

### Layer 2: User Preferences (Personalization)

**Purpose:** What matters to this specific user

**Implementation:**
- Database storage: `users.settings_json` and `users.importance_weights_json`
- Updated through consolidation process
- Used by ranking engine

**Data Structure:**
```json
{
  "topics": {
    "AI agents": 0.9,
    "memory systems": 0.85,
    "startups": 0.7,
    "family logistics": 0.8,
    "sports": 0.1
  },
  "vip_people": [
    "alice@company.com",
    "bob@investor.com",
    "spouse@email.com"
  ],
  "source_trust": {
    "gmail": 1.0,
    "calendar": 1.0,
    "twitter": 0.6,
    "linkedin": 0.7,
    "rss_techcrunch": 0.5
  },
  "content_preferences": {
    "verbosity": "concise",
    "language": "en",
    "max_items_per_module": 5
  }
}
```

**Key Operations:**
- `get_topic_weight(topic)` → float (0.0-1.0)
- `is_vip(person)` → boolean
- `get_source_trust(source)` → float (0.0-1.0)

### Layer 3: Interaction History (Learning Loop)

**Purpose:** Track behavior to learn preferences

**Implementation:**
- Database storage: `feedback_events` table
- Append-only log of interactions
- Analyzed periodically for consolidation

**Data Structure:**
```sql
CREATE TABLE feedback_events (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR,
  item_id VARCHAR,
  event_type VARCHAR,  -- 'open', 'save', 'dismiss', 'thumb_up', 'thumb_down'
  created_at_utc TIMESTAMP,
  payload_json JSON
);
```

**Event Types:**
- `open`: User clicked to view full content
- `save`: User explicitly saved item
- `dismiss`: User dismissed item from view
- `thumb_up`: Positive feedback
- `thumb_down`: Negative feedback
- `less_like_this`: User wants less of this type

---

## 4. Novelty Detection (3 Labels)

Every item gets labeled before ranking:

### Label: NEW
**Condition:** Fingerprint has never been seen  
**Action:** Show it (if ranked high enough)  
**Reason:** "First time seeing this"

### Label: UPDATED
**Condition:** Fingerprint seen before, but content_hash changed  
**Action:** Show it (if ranked high enough)  
**Reason:** "Content changed since {last_seen_date}"

### Label: REPEAT
**Condition:** Fingerprint and content_hash match previous record  
**Action:** Filter out (don't show again)  
**Reason:** "Seen {count} times, last on {date}"

### Implementation

```python
def detect_novelty(user_id: str, item: BriefItem) -> NoveltyLabel:
    """Detect if item is NEW, UPDATED, or REPEAT"""
    
    # Generate stable fingerprint
    fingerprint = generate_fingerprint(item.source, item.type, item.data)
    content_hash = hash_content(item.data)
    
    # Check memory
    memory = load_user_memory(user_id)
    
    if fingerprint not in memory:
        # Never seen before
        record_item(user_id, fingerprint, content_hash)
        return NoveltyLabel.NEW
    
    prev_record = memory[fingerprint]
    
    if prev_record.content_hash != content_hash:
        # Content changed
        update_item(user_id, fingerprint, content_hash)
        return NoveltyLabel.UPDATED
    
    # Same as before
    update_seen_count(user_id, fingerprint)
    return NoveltyLabel.REPEAT
```

### Fingerprinting Strategy

**Goal:** Stable ID that survives fetches but changes when item identity changes

**Approach by source:**

| Source | Primary ID | Fallback |
|--------|-----------|----------|
| Gmail | `message_id` | hash(subject + timestamp) |
| Calendar | `event_id` | hash(title + start_time) |
| Tasks | `task_id` | hash(title) |
| Twitter | `post_id` | hash(author + content + timestamp) |
| LinkedIn | `post_id` | hash(author + content + timestamp) |
| arXiv | `arxiv_id` | N/A (always has ID) |

**Content Hash:** Hash of mutable fields (title, summary, description, status, dates) to detect meaningful changes.

---

## 5. Consolidation Rules (Learning from Behavior)

**When:** Run consolidation weekly (batch job) or after N feedback events

**Input:** All feedback events since last consolidation

**Output:** Updated user preferences (topic weights, VIPs, source trust)

### Rule 1: Topic Weight Adjustment

```python
def consolidate_topics(user_id: str, feedback_events: List[FeedbackEvent]):
    """Learn which topics matter to user"""
    
    preferences = load_user_preferences(user_id)
    
    for event in feedback_events:
        item = get_item(event.item_id)
        topics = extract_topics(item)
        
        for topic in topics:
            # Initialize if new topic
            if topic not in preferences.topics:
                preferences.topics[topic] = 0.5
            
            # Adjust based on feedback
            if event.type in ['save', 'open', 'thumb_up']:
                preferences.topics[topic] += 0.1  # Positive signal
            elif event.type in ['dismiss', 'thumb_down', 'less_like_this']:
                preferences.topics[topic] -= 0.05  # Negative signal
            
            # Clamp to [0.0, 1.0]
            preferences.topics[topic] = max(0.0, min(1.0, preferences.topics[topic]))
    
    save_user_preferences(user_id, preferences)
```

### Rule 2: VIP Auto-Promotion

```python
def consolidate_vips(user_id: str, feedback_events: List[FeedbackEvent]):
    """Promote frequently-engaged people to VIP status"""
    
    preferences = load_user_preferences(user_id)
    
    # Count engagement per person (last 30 days)
    person_engagement = defaultdict(int)
    
    for event in feedback_events:
        if event.type in ['save', 'open', 'thumb_up']:
            item = get_item(event.item_id)
            people = extract_people(item)  # From sender, author, attendees, etc.
            
            for person in people:
                person_engagement[person] += 1
    
    # Promote to VIP if engaged 3+ times
    for person, count in person_engagement.items():
        if count >= 3 and person not in preferences.vip_people:
            preferences.vip_people.append(person)
            print(f"Promoted {person} to VIP (engaged {count} times)")
    
    save_user_preferences(user_id, preferences)
```

### Rule 3: Source Trust Learning

```python
def consolidate_source_trust(user_id: str, feedback_events: List[FeedbackEvent]):
    """Learn which sources produce valuable content"""
    
    preferences = load_user_preferences(user_id)
    
    # Calculate engagement rate per source
    source_stats = defaultdict(lambda: {'shown': 0, 'engaged': 0})
    
    for event in feedback_events:
        item = get_item(event.item_id)
        source = item.source
        
        source_stats[source]['shown'] += 1
        
        if event.type in ['save', 'open', 'thumb_up']:
            source_stats[source]['engaged'] += 1
    
    # Update trust based on engagement rate
    for source, stats in source_stats.items():
        if stats['shown'] >= 5:  # Minimum sample size
            engagement_rate = stats['engaged'] / stats['shown']
            
            # Initialize if new
            if source not in preferences.source_trust:
                preferences.source_trust[source] = 0.5
            
            # Move trust toward engagement rate (smoothed)
            current = preferences.source_trust[source]
            preferences.source_trust[source] = 0.7 * current + 0.3 * engagement_rate
    
    save_user_preferences(user_id, preferences)
```

### Consolidation Schedule

**Trigger consolidation when:**
1. Every 7 days (scheduled)
2. User provides 20+ feedback events since last run
3. User explicitly requests "retrain preferences"

**Safety:**
- Never delete learned preferences entirely
- Decay unused topics slowly (0.99x per week)
- Allow manual override via settings UI

---

## 6. Explainability (Why Shown)

Every item includes a `why_shown` explanation:

```json
{
  "item_ref": "email:abc123",
  "title": "Q4 Planning Meeting - Time Change",
  "novelty": {
    "label": "UPDATED",
    "reason": "Content changed since 2026-01-18"
  },
  "ranking": {
    "final_score": 0.87,
    "breakdown": {
      "relevance": 0.9,
      "urgency": 0.95,
      "credibility": 1.0,
      "actionability": 0.8,
      "impact": 0.7
    }
  },
  "why_shown": {
    "novelty": "UPDATED",
    "top_reasons": [
      "VIP sender: alice@company.com",
      "High urgency: Meeting in 4 hours",
      "Topic match: Q4 planning (weight: 0.85)",
      "Calendar event changed"
    ],
    "confidence": 0.87
  }
}
```

**Display in UI:**
```
📧 Q4 Planning Meeting - Time Change
   From: alice@company.com (VIP)
   
   ℹ️ Shown because:
   • Meeting changed - now starts at 3 PM (was 2 PM)
   • VIP sender
   • High urgency: starts in 4 hours
   • Matches your interest: Q4 planning
```

---

## 7. Implementation Phases

### Phase 1: MVP (Current Implementation) ✅

**Status:** Complete and working

**Components:**
- ✅ Fingerprinting (`packages/memory/fingerprint.py`)
- ✅ Memory manager (`packages/memory/memory_manager.py`)
- ✅ Novelty detection (`packages/memory/novelty.py`)
- ✅ Database persistence (`models.py`: items, item_states, feedback_events)
- ✅ Manual user preferences (set via API)

**What works:**
- Items are fingerprinted and tracked
- NEW/UPDATED/REPEAT labeling works correctly
- Repeats are filtered out
- Feedback events are stored

**What's missing:**
- ❌ No automatic consolidation
- ❌ Topic weights are static
- ❌ VIP list is manual
- ❌ Source trust is not learned

### Phase 2: Basic Consolidation 🎯 (Next Priority)

**Goal:** Learn from user behavior automatically

**Add:**
1. Consolidation service (`packages/memory/consolidator.py`)
2. Topic weight learning (Rule 1)
3. VIP auto-promotion (Rule 2)
4. Source trust learning (Rule 3)
5. Scheduled consolidation job (weekly cron)

**Implementation:**
```python
# packages/memory/consolidator.py

class MemoryConsolidator:
    """Learns user preferences from feedback"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def consolidate_user(self, user_id: str, since_date: datetime):
        """Run consolidation for one user"""
        
        # Get feedback events since last consolidation
        events = self.db.query(FeedbackEvent).filter(
            FeedbackEvent.user_id == user_id,
            FeedbackEvent.created_at_utc >= since_date
        ).all()
        
        if len(events) < 5:
            return  # Not enough data
        
        # Load current preferences
        user = self.db.query(User).filter_by(id=user_id).first()
        prefs = user.settings_json or {}
        
        # Apply consolidation rules
        prefs = self.consolidate_topics(user_id, events, prefs)
        prefs = self.consolidate_vips(user_id, events, prefs)
        prefs = self.consolidate_source_trust(user_id, events, prefs)
        
        # Save updated preferences
        user.settings_json = prefs
        self.db.commit()
        
        return {
            'events_processed': len(events),
            'topics_updated': len(prefs.get('topics', {})),
            'vips_added': len(prefs.get('vip_people', [])),
        }
```

**Schedule:**
```python
# backend/scripts/run_consolidation.py

def consolidate_all_users():
    """Weekly consolidation job"""
    users = db.query(User).all()
    
    for user in users:
        # Consolidate last 7 days
        since = datetime.now(timezone.utc) - timedelta(days=7)
        
        consolidator = MemoryConsolidator(db)
        result = consolidator.consolidate_user(user.id, since)
        
        print(f"User {user.id}: {result}")

# Run via cron: 0 2 * * 0  (2 AM every Sunday)
```

### Phase 3: Advanced Features 🚀 (Future)

**Semantic Deduplication:**
- Add vector DB (Qdrant)
- Embedding-based similarity detection
- Cluster "same story, different source"

**Entity-Aware Updates:**
- Track entities across items
- Detect "new information about known topic"
- Timeline reconstruction

**Predictive Importance:**
- Train ML model on feedback
- Predict importance before showing
- Active learning: show uncertain items to learn

**Narrative Context:**
- Monthly "state of your world" summary
- Project timelines
- Recurring theme detection

---

## 8. Data Flows

### Flow 1: Daily Brief Generation

```
1. Orchestrator triggers brief run
   ↓
2. Connectors fetch raw items (Gmail, Twitter, etc.)
   ↓
3. Normalizer converts to BriefItem format
   ↓
4. NoveltyDetector labels each item (NEW/UPDATED/REPEAT)
   ↓
5. Filter: Keep only NEW and UPDATED
   ↓
6. Ranker scores items using user preferences
   ↓
7. Selector picks top N items per module
   ↓
8. Synthesizer adds "why it matters"
   ↓
9. BriefBundle assembled and returned
   ↓
10. Store bundle in database
```

### Flow 2: User Feedback Loop

```
1. User interacts with item (click, save, dismiss)
   ↓
2. Frontend sends feedback event to API
   ↓
3. Store in feedback_events table
   ↓
4. Update item_states (mark as seen, saved, etc.)
   ↓
5. [Async] Count feedback events since last consolidation
   ↓
6. [Weekly] If threshold reached, trigger consolidation
   ↓
7. Consolidator analyzes events
   ↓
8. Update user preferences (topics, VIPs, trust)
   ↓
9. Next brief uses updated preferences for ranking
```

### Flow 3: Memory Lookup

```
When checking if item is new:

1. Generate fingerprint from item data
   ↓
2. Load user's memory file (memoized)
   ↓
3. Check if fingerprint exists
   ↓
4. If yes: Compare content_hash
   ↓
5. Return: NEW | UPDATED | REPEAT
   ↓
6. Update memory record (seen_count, last_seen)
   ↓
7. Save memory file (batched)
```

---

## 9. Storage Details

### Filesystem Memory (`memory_store/`)

**Location:** `{project_root}/memory_store/{user_id}_memory.json`

**Why filesystem?**
- Fast read/write for frequent lookups
- Easy to inspect and debug
- Portable (can backup/restore easily)
- No database load for novelty checks

**Structure:**
```json
{
  "fingerprint1": {
    "fingerprint": "email:abc123",
    "content_hash": "xyz789",
    "first_seen_utc": "...",
    "last_seen_utc": "...",
    "seen_count": 3,
    "source": "gmail",
    "item_type": "email",
    "title": "Meeting reminder"
  },
  "fingerprint2": { ... },
  ...
}
```

**Maintenance:**
- Prune items not seen in 90 days
- Keep file size under 10 MB per user
- Backup weekly to database or S3

### Database Memory (`postgres`)

**Tables:**

**users:**
- `id`, `timezone`, `created_at`
- `settings_json`: User preferences (topics, VIPs, sources)
- `importance_weights_json`: Custom ranking weights
- `last_brief_timestamp_utc`: For incremental fetching

**items:**
- Canonical item records (deduplicated)
- Indexed by `user_id`, `source`, `source_id`, `timestamp`
- Used for consolidation analysis

**item_states:**
- Per-user state: seen, saved, ignored
- Feedback scores
- Open counts

**feedback_events:**
- Append-only log
- Used for consolidation
- Retention: 90 days

**brief_bundles:**
- Historical briefs
- Used for "what did I see before?"
- Retention: 30 days

---

## 10. Performance Considerations

### Memory Lookups

**Challenge:** Checking novelty for 100+ items per brief

**Solution:**
- Load user memory once per brief run
- Batch all novelty checks
- Write memory once at end (not per item)

**Code:**
```python
# Bad: Load/save per item
for item in items:
    memory = load_memory(user_id)  # ❌ 100 reads
    check_novelty(item, memory)
    save_memory(user_id, memory)   # ❌ 100 writes

# Good: Batch processing
memory = load_memory(user_id)      # ✅ 1 read
for item in items:
    check_novelty(item, memory)
save_memory(user_id, memory)       # ✅ 1 write
```

### Consolidation

**Challenge:** Analyzing thousands of feedback events

**Solution:**
- Run async (don't block brief generation)
- Process per user (parallelizable)
- Incremental: only events since last run
- Cache aggregations

### Database Queries

**Indexes needed:**
```sql
CREATE INDEX idx_items_user_source ON items(user_id, source);
CREATE INDEX idx_feedback_user_time ON feedback_events(user_id, created_at_utc);
CREATE INDEX idx_item_states_user ON item_states(user_id);
```

---

## 11. Testing Strategy

### Unit Tests

**Test fingerprinting:**
```python
def test_stable_fingerprint():
    """Same item data → same fingerprint"""
    item1 = {'id': 'msg123', 'subject': 'Test'}
    item2 = {'id': 'msg123', 'subject': 'Test'}
    
    fp1 = generate_fingerprint('gmail', 'email', item1)
    fp2 = generate_fingerprint('gmail', 'email', item2)
    
    assert fp1 == fp2
```

**Test novelty detection:**
```python
def test_novelty_new_item():
    """First time seeing item → NEW"""
    detector = NoveltyDetector()
    item = create_test_item()
    
    novelty = detector.detect_novelty('user123', item)
    
    assert novelty.label == 'NEW'
    assert 'First time' in novelty.reason
```

**Test consolidation:**
```python
def test_topic_weight_increase():
    """Saving item → increase topic weight"""
    consolidator = MemoryConsolidator()
    
    # User saves AI article
    events = [create_save_event(item_with_topic='AI')]
    prefs = {'topics': {'AI': 0.5}}
    
    new_prefs = consolidator.consolidate_topics('user123', events, prefs)
    
    assert new_prefs['topics']['AI'] > 0.5
```

### Integration Tests

**End-to-end brief generation:**
```python
def test_brief_filters_repeats():
    """REPEAT items are filtered out"""
    # First brief
    brief1 = generate_brief('user123')
    assert len(brief1.items) == 5
    
    # Second brief (same data)
    brief2 = generate_brief('user123')
    assert len(brief2.items) == 0  # All repeats
```

### Manual Testing Scenarios

1. **Novelty accuracy:**
   - Send test email → Should appear as NEW
   - Fetch again → Should be REPEAT
   - Change subject → Should be UPDATED

2. **Consolidation behavior:**
   - Save 3 AI articles → Check topic weight increased
   - Dismiss 3 sports posts → Check topic weight decreased
   - Engage with person 3x → Check VIP list

3. **Explainability:**
   - View brief → Each item should have clear "why shown"
   - Dismiss item → Should see less of that topic next time

---

## 12. Migration from Current State

**Current implementation (MVP) → Simplified design:**

**What stays the same:**
- ✅ Fingerprinting logic (`fingerprint.py`)
- ✅ Memory manager filesystem storage (`memory_manager.py`)
- ✅ Novelty detection (`novelty.py`)
- ✅ Database models (`models.py`)

**What to add:**
1. Create `packages/memory/consolidator.py`
2. Add consolidation rules (topics, VIPs, trust)
3. Create weekly cron job
4. Update ranking to use learned preferences
5. Add "why shown" to BriefItem output

**Migration path:**
```bash
# Phase 1: Add consolidator (no breaking changes)
# - Add consolidator.py
# - Add consolidation endpoint
# - Test manually

# Phase 2: Enable automatic learning
# - Add cron job
# - Monitor preference changes
# - A/B test with/without consolidation

# Phase 3: UI for preferences
# - Show learned topics in settings
# - Allow manual override
# - "Retrain preferences" button
```

---

## 13. Success Metrics

**Novelty accuracy:**
- Target: < 1% false duplicates (items marked NEW that were REPEAT)
- Target: > 95% true positives (actual new items marked NEW)

**Personalization effectiveness:**
- Engagement rate increase: +20% after 2 weeks of learning
- Dismissed items decrease: -30% after consolidation
- User satisfaction: > 80% say "brief got better over time"

**Performance:**
- Memory lookup: < 100ms for 100 items
- Consolidation: < 5 seconds per user
- Brief generation: < 30 seconds total

---

## 14. Future Enhancements

### Short-term (3-6 months)
- Add "retrain preferences" button in UI
- Show learned preferences in settings
- Email digest of consolidation changes
- A/B test consolidation frequency

### Medium-term (6-12 months)
- Semantic deduplication with embeddings
- Cross-source entity tracking
- Predictive importance scoring
- Mobile push notifications for high-urgency items

### Long-term (12+ months)
- Multi-user briefs (team mode)
- Conversational memory ("What did I see about X?")
- Proactive suggestions ("Based on your calendar...")
- Memory export/import (user data portability)

---

## 15. References

**Related Documentation:**
- [memory.md](./memory.md) - Brain-inspired conceptual design
- [implementation_spec.md](./implementation_spec.md) - Full system spec
- [arch.md](./arch.md) - Architecture overview

**Current Implementation:**
- `backend/packages/memory/` - Memory system code
- `backend/packages/ranking/` - Importance scoring
- `backend/packages/database/models.py` - Data models

**Key Concepts:**
- **Fingerprint:** Stable ID for item identity
- **Content hash:** Hash for detecting changes
- **Novelty label:** NEW, UPDATED, or REPEAT
- **Consolidation:** Learning preferences from behavior
- **Episodic memory:** What you've seen (short-term)
- **Semantic memory:** What you care about (long-term)

---

**Last Updated:** 2026-01-19  
**Status:** ✅ Aligned with current MVP implementation  
**Next Steps:** Implement Phase 2 consolidation rules
