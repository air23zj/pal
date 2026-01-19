([Past chat][1])([Past chat][2])([Past chat][3])([Past chat][4])([Past chat][5])

Alright — let’s design **Morning Brief’s memory system** using the same **brain-inspired “Her” framework** (Hippocampus / Neocortex / PFC / Amygdala + write-gating + consolidation).

The key difference vs a chat assistant: Morning Brief is **time-series + delta-oriented**. So memory isn’t just “what’s true about the user”, it’s “what changed since last brief” + “what matters”.

Below is a **world-class, implementable memory design**.

---

# Morning Brief Memory System (Brain-Inspired)

## Goals (what memory must enable)

1. **Novelty**: never show repeats; detect real “updates”
2. **Importance**: show only what’s meaningful to *you*
3. **Continuity**: preserve ongoing themes + open loops across days
4. **Personalization**: learn your preferences from feedback/behavior
5. **Trust**: explain “why shown” + evidence + edit/delete memory

---

# Brain Modules Mapping

## 1) Hippocampus = Episodic Memory (Daily Brief Ledger)

**Purpose:** fast-write, time-indexed memory of “what happened / what was shown / what you consumed”.

### Stores (Episodic)

* Every briefing run (“episode”)
* Every candidate item surfaced + its novelty label
* Your interactions (open/save/dismiss/thumbs)
* Last-seen timestamps per source + per entity
* Evidence pointers (URLs/snippets, not full content)

### Why Hippocampus matters here

This is the **core anti-repeat / novelty engine**:

* “Have I shown this already?”
* “Did I see this yesterday?”
* “Is this a new event, or just more posts about the same thing?”

---

## 2) Neocortex = Semantic Memory (Stable Preferences + Knowledge)

**Purpose:** slow-changing “what I care about” and “how I define important”.

### Stores (Semantic)

* Interest topics + weights (agents, memory, startups, family logistics, etc.)
* VIP people graph (team, investors, close friends)
* Source trust weights (Bloomberg > random blog; close friend > influencer)
* Content style preferences (short vs deep, tech vs business)
* “Importance rules” distilled from feedback

### Example semantic facts

* “User cares about *agent infrastructure + memory + WeChat mini-program super-app agents*”
* “Show arXiv papers only if top-tier relevance”
* “Calendar changes within 24h are critical”

---

## 3) PFC = Executive Memory (Planning + Gating + VOI)

**Purpose:** decides what to retrieve, what to show, what to ask, what to suppress.

### Responsibilities

* Set budgets: time/cost/item caps
* Decide which sources to query today (VOI-driven)
* Decide which updates become **Top Highlights**
* Decide whether an item triggers an **Action suggestion**
* Decide memory write policy: STORE / IGNORE / DEFER / ASK_CONSENT

In Morning Brief terms:

> **PFC is the “brief editor-in-chief.”**

---

## 4) Amygdala = Salience + Affect Tags (Importance Bias)

**Purpose:** tag items with emotional/urgency weight, so memory prioritizes what matters.

In Morning Brief, “affect” isn’t emotional drama — it’s **salience**:

* urgency (today / soon)
* risk (if missed → bad)
* opportunity (if acted → upside)
* personal significance (family / VIP / deadlines)

This drives:

* what gets shown
* what gets promoted to long-term memory
* what breaks through “noise suppression”

---

# Memory Types (Morning Brief Specific)

We keep the same memory categories as “Her” but tuned:

## A) Episodic (Hippocampus)

* `BriefEpisode` (daily run summary)
* `PresentedItem` (what you saw)
* `InteractionEvent` (your behavior)
* `SourceCursor` (last checked timestamps per source)

## B) Semantic (Neocortex)

* `UserTopicProfile` (topics + weights)
* `VIPGraph` (people/org/project relations)
* `SourceTrustProfile`
* `PreferenceRules` (“show less sports, more research”)

## C) Procedural (Skills)

* “How to scan X efficiently”
* “How to interpret arXiv results for user”
* “How to filter LinkedIn noise”
  This lives as **agent skills + prompts** rather than user memory, but can be referenced.

## D) Commitments / Intent (Open loops)

* “Need to reply to Sarah today”
* “Follow up on sandbox decision”
* “Prepare for meeting”
  Commitments are critical because they determine urgency.

---

# The Canonical Memory Object (portable across DB + filesystem)

Use a single internal model: **MemoryItem**.

```json
{
  "memory_id": "mem_01H...",
  "type": "episodic|semantic|commitment|procedural",
  "domain": "news|social|research|inbox|calendar|family|health",
  "content": { "title": "...", "summary": "...", "payload": {} },

  "fingerprints": {
    "source": "x|linkedin|gmail|arxiv|rss",
    "source_id": "msgid/arxiv_id/url_hash",
    "semantic_hash": "optional"
  },

  "entities": ["person:alice", "project:morning-brief", "topic:agents"],
  "timestamps": {
    "created_utc": "...",
    "last_seen_utc": "...",
    "expires_utc": null
  },

  "salience": {
    "importance": 0.0,
    "urgency": 0.0,
    "risk": 0.0,
    "opportunity": 0.0
  },

  "provenance": {
    "evidence_urls": ["..."],
    "confidence": 0.0
  },

  "policy": {
    "sensitivity": "normal|high",
    "write_decision": "store|ignore|defer|ask_consent"
  }
}
```

---

# Retrieval: “MemoryContextPack” for Morning Brief Runs

Each daily run builds a **MemoryContextPack**:

### 1) Active Semantic Frame (Neocortex)

* topic weights
* VIP list + relationships
* source weights
* preference rules

### 2) Recent Episodes (Hippocampus, last 7–14 days)

* what was shown
* what was clicked/saved/dismissed
* last check times per source

### 3) Active Commitments

* emails needing response
* tasks due
* meetings within 24h
* unresolved “open loops”

### 4) NarrativeBrief (compressed “who you are this month”)

This is the personalized backbone:

* current themes
* current projects
* recurring routines
* recent wins/losses
* what to pay attention to

This keeps the brief coherent over weeks.

---

# Write Policy (STORE / IGNORE / DEFER / ASK_CONSENT)

Reusing “Her” write gating, tuned for briefing:

### Candidate memories come from:

* each ingestion agent (news/social/research/etc.)
* ranking engine (importance signals)
* UI interactions (save/dismiss/thumbs)
* system events (brief generated)

### Write decision logic (fast rule)

**STORE if**:

* item was shown in Top Highlights, OR
* user saved/opened, OR
* high urgency/commitment, OR
* repeated relevance across days (promote)

**IGNORE if**:

* low signal, or repeat, or low confidence

**DEFER if**:

* uncertain relevance but might matter (store short-lived in STM only)

**ASK_CONSENT if**:

* sensitive personal content (health, finances, private family details)
  Even if it’s “useful,” don’t silently persist.

---

# Consolidation (Hippocampus → Neocortex)

This is *the* brain-inspired trick that makes personalization real.

### Promotion rules

* If an item pattern appears **3+ times in 14 days** and user engages → promote to semantic preference
* If user repeatedly dismisses a topic/source → downweight permanently
* If person repeatedly triggers action → promote to VIP or high priority entity

### Example consolidation outputs

* “You care about agent memory papers more than general AI news”
* “LinkedIn posts from 5 specific people have high value”
* “Commute + weather are always top-row items”

---

# Novelty Detection (the “Hippocampus job”)

## Tier 1: Exact Novelty

* same `source_id` (email msg-id, arxiv-id, URL hash) → repeat

## Tier 2: Semantic Novelty

* embedding similarity > threshold → repeat/duplicate cluster

## Tier 3: Update Novelty

Mark `UPDATED` if:

* same entities/topic cluster
* but new key facts / new timestamp / new action requirement

**Important**: UPDATED must be *meaningful delta* or it becomes noise.

---

# Storage Design (Practical Implementation)

## Source of truth

* **Postgres** = canonical storage for items + states + feedback
* **Filesystem** = portable memory + agent-local working set + append-only logs
* **Vector DB (later)** = semantic dedupe / retrieval

### Suggested split

**Postgres**

* items
* item_states (seen/saved/ignored)
* brief_bundles
* feedback_events
* user settings

**Filesystem**

* last_brief_timestamp
* seen_fingerprints.log (fast append)
* episodes snapshots (optional)
* narrative_brief.md / json

---

# Concrete Directory Layout (Brain Labels)

```txt
/memory
  /hippocampus
    episodes/
      2026-01-18.brief.json
    seen_fingerprints.log
    source_cursors.json
    interactions.log

  /neocortex
    topics.json
    vip_people.json
    source_trust.json
    preference_rules.md
    narrative_brief.md

  /pfc
    budgets.json
    retrieval_policy.json
    ranking_weights.json

  /amygdala
    salience_models.json
    alert_thresholds.json
```

This is clean, debuggable, and maps directly to your “Her” mental model.

---

# “Why Shown” Explainability (Trust Layer)

Every surfaced item should store:

* novelty reason: `NEW / UPDATED`
* top factors: `VIP + urgent + topic match + action required`
* evidence URL(s)
* confidence estimate

This enables a transparent UI:

* “Shown because: VIP mention + deadline today + new since last brief.”

---

# What’s “World Class” Here (vs typical apps)

### Most dashboards fail because they treat memory as:

* bookmarks
* history
* embeddings

**You’re treating memory as a *brain system*:**

* episodic → semantic consolidation
* salience-driven prioritization
* executive gating
* explainability
* consent-aware persistence

That’s exactly the right moat.

---

# Minimal MVP Implementation Checklist (Memory-First)

If you want to build the correct MVP without overbuilding:

✅ Implement these first:

1. Hippocampus `seen_fingerprints` + `source_cursors`
2. item_states in Postgres
3. novelty labeling NEW/UPDATED/REPEAT
4. consolidation rule: “repeated engagement → higher topic weight”
5. narrative brief generation (even simple)

Everything else can come later.

---
