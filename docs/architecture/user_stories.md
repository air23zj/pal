# Morning Brief AGI — User Stories

**File:** `docs/user_stories.md`  
**Status:** Draft v1.0  
**Scope:** MVP → V2 (mapped to epics, stories, acceptance criteria)

---

## 0) Conventions

### Priority
- **P0**: Must ship for MVP
- **P1**: V1 (next)
- **P2**: V2 (later)

### Story format
- **As a** <persona>  
- **I want** <capability>  
- **So that** <outcome>  
- **Acceptance criteria**: bullet list

### Personas
- **Power user / builder / researcher**
- **Exec / manager**
- **Family coordinator**

---

## 1) EPIC: Brief Generation & Dashboard Core (MVP)

### MB-001 (P0) View latest brief instantly
**As a** user  
**I want** the dashboard to load the latest brief immediately  
**So that** I can scan my day in seconds

**Acceptance criteria**
- Dashboard shows cached latest brief within 2 seconds
- If no brief exists, shows a valid empty-state brief (not an error)
- Modules render even if some are degraded/error/skipped

---

### MB-002 (P0) Generate a brief on demand
**As a** user  
**I want** a “Refresh” action to generate a new brief  
**So that** I can update my morning plan anytime

**Acceptance criteria**
- Refresh triggers an async run and does not freeze UI
- UI shows progress state (e.g., “Generating…”)
- New brief replaces old only after validation succeeds

---

### MB-003 (P0) Generate daily brief automatically at 6:00 AM
**As a** user  
**I want** a daily scheduled brief  
**So that** it’s ready when I wake up

**Acceptance criteria**
- Scheduler triggers at 6:00 AM in user timezone
- If a run fails, last successful timestamp is not advanced
- A valid brief is persisted each day (ok or degraded)

---

### MB-004 (P0) Top highlights are concise and limited
**As a** user  
**I want** at most five top highlights  
**So that** I get signal without overwhelm

**Acceptance criteria**
- Top highlights ≤ 5 always
- Each highlight has: title, one-line summary, why-it-matters, evidence
- Highlights are ranked by final_score and salience

---

### MB-005 (P0) Modules show only new and important items
**As a** user  
**I want** each module to show only new/updated items  
**So that** I don’t waste time rereading repeats

**Acceptance criteria**
- Module shows NEW/UPDATED only by default
- Total items across dashboard ≤ 30
- Module cap ≤ 8 items (default view ≤ 3; expand available)

---

### MB-006 (P0) Deep dive into an item with evidence
**As a** user  
**I want** to open an item to see details and sources  
**So that** I can trust and verify the summary

**Acceptance criteria**
- Deep dive view shows evidence URLs/snippets
- Displays why-shown factors (topic match, VIP, urgency, etc.)
- Opening increments opened_count for that item

---

---

## 2) EPIC: Novelty Detection (Anti-Repeat) & Memory (MVP)

### MB-010 (P0) Never show the same content twice
**As a** user  
**I want** the system to remember what I’ve already seen  
**So that** my brief stays high-signal

**Acceptance criteria**
- Exact dedupe by source_id/url_hash prevents repeats
- Repeat rate trends < 10% after 2 days of usage
- User can mark item “seen” to suppress it immediately

---

### MB-011 (P0) Detect meaningful updates
**As a** user  
**I want** “UPDATED” items only when something actually changed  
**So that** updates remain meaningful rather than noise

**Acceptance criteria**
- UPDATED requires entity overlap + newer timestamp + content delta threshold
- Updated items include a short “what changed” note when possible
- Updated items are suppressed if delta is trivial

---

### MB-012 (P0) Track source cursors per integration
**As a** user  
**I want** the system to track the last time each source was checked  
**So that** “since last brief” is accurate

**Acceptance criteria**
- Persist per-source timestamps in memory
- On successful run, source cursors advance
- On failed run, cursors do not advance

---

### MB-013 (P0) Store episodic history of briefs
**As a** user  
**I want** the system to keep a record of my past briefs  
**So that** it can support continuity and retrospectives

**Acceptance criteria**
- Each run stores a brief bundle snapshot (episode)
- The last 7–14 days are accessible for dedupe and continuity
- Storage avoids saving full raw content unnecessarily

---

---

## 3) EPIC: Personalization & Learning (MVP → V1)

### MB-020 (P0) Preferences setup (topics + sources)
**As a** user  
**I want** to configure topics and toggle sources  
**So that** the brief matches my interests and workflow

**Acceptance criteria**
- Topics can be added/removed/weighted
- Modules can be enabled/disabled
- Disabled modules are marked `skipped` and not fetched

---

### MB-021 (P0) Feedback trains future briefs
**As a** user  
**I want** to give feedback per item  
**So that** relevance improves over time

**Acceptance criteria**
- 👍 increases topic/entity/source weights
- 👎 decreases weights
- “Less like this” reduces similar items noticeably within 1–3 runs
- Feedback events are persisted and auditable

---

### MB-022 (P1) VIP list improves importance ranking
**As a** user  
**I want** to mark people as VIPs  
**So that** their messages and posts surface reliably

**Acceptance criteria**
- VIP mentions boost relevance score
- VIP-triggered items can appear in Top Highlights
- VIP list editable in settings

---

### MB-023 (P1) Consolidate patterns into long-term preferences
**As a** user  
**I want** the system to learn durable preferences  
**So that** I don’t have to keep tuning it manually

**Acceptance criteria**
- Repeated engagement pattern (e.g., 3+ times/14 days) promotes to semantic profile
- Repeated dismissals demote or mute sources/topics
- Consolidation job runs on a schedule (e.g., nightly)

---

---

## 4) EPIC: Integrations via MCP (MVP)

### MB-030 (P0) Gmail delta: important emails since last brief
**As a** user  
**I want** only important new emails surfaced  
**So that** I don’t scan my whole inbox

**Acceptance criteria**
- Shows emails requiring action / from VIPs / time-sensitive
- Marks module degraded if MCP not available
- Provides “Open in Gmail” evidence links

---

### MB-031 (P0) Calendar: today + tomorrow with prep cues
**As a** user  
**I want** calendar events with practical context  
**So that** I’m prepared for my day

**Acceptance criteria**
- Shows next meetings + time + location
- Flags meetings within 2 hours as urgent
- Module works degraded if integration missing

---

### MB-032 (P0) Tasks: due today + overdue
**As a** user  
**I want** tasks due today and overdue  
**So that** I don’t miss commitments

**Acceptance criteria**
- Due today surfaced in Work Focus
- Overdue items flagged
- Module degraded if MCP missing

---

### MB-033 (P1) Keep notes: resurface relevant notes
**As a** user  
**I want** relevant notes resurfaced based on today’s context  
**So that** I remember what matters when it matters

**Acceptance criteria**
- Notes match today’s meetings/projects/topics
- User can pin notes to always appear
- Notes storage respects privacy controls

---

---

## 5) EPIC: Content Sources (MVP)

### MB-040 (P0) News RSS ingestion
**As a** user  
**I want** curated news highlights  
**So that** I stay informed without doomscrolling

**Acceptance criteria**
- Configurable RSS sources
- Dedup cross-sources (same story multiple feeds)
- Evidence links to original articles

---

### MB-041 (P0) arXiv research radar
**As a** user  
**I want** new relevant papers  
**So that** I keep up with research in my topics

**Acceptance criteria**
- Keyword/topic matching
- Dedup by arXiv id
- “Why it matters” ties back to user topics

---

---

## 6) EPIC: Logistics & Life Modules (MVP Stubs → V1)

### MB-050 (P0) Weather “impact” module (stub OK)
**As a** user  
**I want** weather information framed by impact  
**So that** I can plan clothing and timing

**Acceptance criteria**
- Module present even if data source not wired (empty state)
- Later: shows rain windows, temp changes, advisories

---

### MB-051 (P0) Commute module (stub OK)
**As a** user  
**I want** commute time and recommended departure  
**So that** I arrive on time

**Acceptance criteria**
- Module present even if empty
- Later: route ETA + delays + suggested departure time

---

### MB-052 (P1) Exercise goal module
**As a** user  
**I want** exercise goals and a suggested plan  
**So that** health stays on track

**Acceptance criteria**
- Shows goal progress
- Suggests a realistic plan based on schedule constraints

---

### MB-053 (P2) Family activities module
**As a** user  
**I want** family logistics in one place  
**So that** I don’t miss pickups, appointments, shared plans

**Acceptance criteria**
- Shared calendar events surfaced
- Sensitive info requires explicit user consent to persist

---

---

## 7) EPIC: Social Agents (V1)

### MB-060 (P1) Scan X for relevant updates (read-only)
**As a** user  
**I want** relevant X updates since last brief  
**So that** I get signal without scrolling

**Acceptance criteria**
- Uses browser-use agent in sandbox
- Enforces read-only (no like/post/comment)
- Extracts relevant posts from VIPs/topics
- Fails gracefully if login/UI change occurs (module degraded)

---

### MB-061 (P1) Scan LinkedIn for relevant updates (read-only)
**As a** user  
**I want** relevant LinkedIn updates since last brief  
**So that** I stay current on my network

**Acceptance criteria**
- Uses browser-use agent in sandbox
- Enforces read-only
- Returns evidence URLs and short snippets
- Degraded fallback on failure

---

---

## 8) EPIC: Podcasts (V1)

### MB-070 (P1) Podcast subscription updates
**As a** user  
**I want** new podcast episodes from my subscriptions  
**So that** I can decide what to listen to

**Acceptance criteria**
- Integrates Spotify/Apple APIs if possible, RSS fallback
- Shows new episodes since last brief
- Provides quick “should listen?” reasoning and runtime

---

---

## 9) EPIC: Realtime & Responsiveness (V1)

### MB-080 (P1) WebSocket updates when new brief is ready
**As a** user  
**I want** the dashboard to update when a run completes  
**So that** refresh feels instant and modern

**Acceptance criteria**
- WebSocket pushes `brief_ready` event
- UI refetches latest brief and shows subtle toast
- Falls back to polling if WS unavailable

---

---

## 10) EPIC: Trust, Safety, and Control (MVP → V2)

### MB-090 (P0) Explain “why shown”
**As a** user  
**I want** to understand why each item was surfaced  
**So that** I trust the system and can tune it

**Acceptance criteria**
- Shows novelty reason + top scoring factors
- Shows evidence and timestamps
- Explanation is concise and grounded

---

### MB-091 (P1) Export and delete memory
**As a** user  
**I want** to export or delete stored memory  
**So that** I control my data

**Acceptance criteria**
- Export includes preferences + item states + episodes (optional)
- Delete removes user data from DB and filesystem memory
- Confirmation and warnings provided

---

### MB-092 (P2) Human-in-loop for high-stakes actions
**As a** user  
**I want** approval gates before the system can take actions  
**So that** nothing irreversible happens without consent

**Acceptance criteria**
- Any write action requires explicit confirm
- Read-only default persists unless user opts in

---

---

## 11) EPIC: V2 Intelligence Upgrades (Later)

### MB-100 (P2) Natural language query interface
**As a** user  
**I want** to ask “Show me research on LLM agents”  
**So that** I can explore beyond the default brief

**Acceptance criteria**
- Returns filtered views over stored items + sources
- Shows evidence and respects privacy settings

---

### MB-101 (P2) Weekly/monthly digest & trend analysis
**As a** user  
**I want** periodic digests  
**So that** I see trends and progress over time

**Acceptance criteria**
- Weekly trends by topic/source/people
- Highlights open loops and recurring issues
- Works even with partial integrations

---

## 12) Backlog Notes (Engineering Tasks Tie-In)

- Align each story with orchestrator nodes:
  - gather → normalize → novelty → rank → select → synthesize → persist
- Each integration must have:
  - degraded mode
  - budget/timeouts
  - tests with mocks

---
