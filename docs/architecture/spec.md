# Morning Brief AGI — Technical Spec Quick Reference

> **For full implementation details, see [implementation_spec.md](./implementation_spec.md)**

This document provides a quick reference for the core technical contracts. For complete schemas, database design, orchestration pipeline, and implementation checklist, see the full implementation spec.

---

## 1) Core Data Contracts

### BriefBundle (Backend → Frontend)

```json
{
  "brief_id": "brief_2026-01-18T07:10:22Z",
  "user_id": "u_123",
  "brief_date_local": "2026-01-18",
  "timezone": "America/Los_Angeles",
  "generated_at_utc": "2026-01-18T15:10:22Z",
  "since_timestamp_utc": "2026-01-17T15:00:00Z",

  "top_highlights": [ /* BriefItem[] max 5 */ ],
  
  "modules": {
    "news": { /* ModuleResult */ },
    "social_x": { /* ModuleResult */ },
    "social_linkedin": { /* ModuleResult */ },
    "research": { /* ModuleResult */ },
    "podcasts": { /* ModuleResult */ },
    "inbox": { /* ModuleResult */ },
    "calendar": { /* ModuleResult */ },
    "todos_notes": { /* ModuleResult */ },
    "commute": { /* ModuleResult */ },
    "weather": { /* ModuleResult */ },
    "family": { /* ModuleResult */ }
  },

  "actions": [ /* Action[] */ ],
  "evidence_log": [ /* EvidenceLog[] */ ],
  
  "run_metadata": {
    "status": "ok",
    "latency_ms": 42000,
    "cost_estimate_usd": 0.42,
    "agents_used": ["news_agent", "brief_editor_agent"],
    "warnings": []
  }
}
```

### ModuleResult (uniform across all modules)

```json
{
  "status": "ok",
  "summary": "2 important updates; 1 requires action today.",
  "new_count": 3,
  "updated_count": 1,
  "items": [ /* BriefItem[] */ ]
}
```

Status values: `ok | degraded | error | skipped`

### BriefItem (uniform across all sources)

```json
{
  "item_ref": "item_arxiv_2401.12345",
  "source": "arxiv",
  "type": "paper",
  "timestamp_utc": "2026-01-18T04:21:00Z",

  "title": "Tool-Augmented Agents with Filesystem Memory",
  "summary": "Proposes a filesystem-based memory layout...",
  "why_it_matters": "Directly impacts your agent memory roadmap.",
  "entities": [
    {"kind": "topic", "key": "agents"},
    {"kind": "topic", "key": "memory"}
  ],

  "novelty": {
    "label": "NEW",
    "reason": "No prior record; new arXiv ID",
    "first_seen_utc": "2026-01-18T14:03:10Z"
  },

  "ranking": {
    "relevance_score": 0.92,
    "urgency_score": 0.15,
    "credibility_score": 0.95,
    "actionability_score": 0.55,
    "final_score": 0.83
  },

  "evidence": [
    {"kind": "url", "title": "arXiv", "url": "https://arxiv.org/abs/2401.12345"}
  ],

  "suggested_actions": [
    {"type": "bookmark", "label": "Save to reading list"}
  ]
}
```

---

## 2) Service Architecture

### Orchestration Pipeline (Custom DAG)

**MVP Flow:**
1. **LoadContext** → Load user profile + determine since_timestamp
2. **GatherCandidates** (parallel) → Gmail, Calendar, Tasks, News, arXiv, Weather, Commute
3. **NormalizeCandidates** → Transform to canonical format + extract entities
4. **NoveltyFilter** → Label as NEW / UPDATED / REPEAT / LOW_SIGNAL
5. **RankImportance** → Compute relevance, urgency, credibility, actionability scores
6. **SelectAndCap** → Apply limits (5 highlights, 3-8 per module, 30 total)
7. **BriefSynthesis** (LLM) → Add "why_it_matters", generate summaries
8. **Persist** → Store bundle, update DB, update filesystem memory
9. **Done** → Return brief_id + status

**V1 Additions:**
- Social X/LinkedIn ingestion (browser-use)
- Podcasts ingestion
- Embeddings + Qdrant semantic dedupe

---

## 3) Novelty & Ranking

### Stable Item IDs
```
stable_id = hash(source + type + source_id)
fallback: hash(url + timestamp_bucket + title)
```

### Novelty Rules
- Exact source_id exists + seen within 14 days → `REPEAT`
- Entity overlap + newer timestamp + delta > threshold → `UPDATED`
- Otherwise → `NEW`

**Only show:** NEW + meaningful UPDATED

### Ranking Formula

```
final_score =
  0.45 * relevance +
  0.20 * urgency +
  0.15 * credibility +
  0.10 * impact_proxy +
  0.10 * actionability
```

### Caps & Budgets
- Highlights: ≤ 5
- Module default view: ≤ 3 items (expand optional)
- Module max: ≤ 8 items
- Total: ≤ 30 items

---

## 4) Agent I/O Contract

### Input to any worker agent

```json
{
  "user_id": "u_123",
  "since_timestamp_utc": "2026-01-17T15:00:00Z",
  "topics": ["agents", "sandboxes", "LLM memory"],
  "preferences": {
    "max_items": 8,
    "verbosity": "tight",
    "language": "en"
  },
  "memory_refs": {
    "stm_path": "/memory/state/",
    "ltm_path": "/memory/profile/"
  },
  "budget": {
    "time_ms": 12000,
    "tokens": 2500
  }
}
```

### Output from any worker agent

```json
{
  "agent": "social_agent_x",
  "status": "ok",
  "candidate_items": [ /* BriefItemCandidate[] */ ],
  "errors": [],
  "stats": { "pages_visited": 6, "items_extracted": 22 }
}
```

---

## 5) Backend API Endpoints

**GET /api/brief/latest** — Returns latest cached BriefBundle

**POST /api/brief/run** — Triggers orchestration run (async), returns run_id

**GET /api/brief/run/{run_id}** — Returns run status + metadata

**GET /api/brief/{brief_id}** — Returns bundle JSON

**POST /api/feedback** — Records user feedback (thumb_up/down, dismiss, etc.)

**POST /api/item/mark_seen** — Marks item as seen immediately

---

## 6) Agent Runtime & LLM Options

### Sandbox Runtime
**Cloud:**
- E2B (serverless sandboxes)
- Firecracker (VM-level isolation)

**Local:**
- open-skills ([github.com/instavm/open-skills](https://github.com/instavm/open-skills))
  - MCP server with container isolation
  - Skills system + browser automation
  - Zero data upload

### LLM Providers
**Cloud:**
- Claude (Anthropic)
- Gemini (Google)
- OpenAI (GPT-4)

**Local:**
- Ollama
- LM Studio

---

## 7) Memory System

### Filesystem Structure
```
/memory
  /user-profile
    interests.json
    interaction-history.json
  /content-tracking
    seen-fingerprints.log
    temporal-markers.json
  /learning
    relevance-signals.json
    entity-graph.json
  /episodes
    YYYY-MM-DD.brief.json
```

### Responsibilities
- Deduplication (never show twice)
- Novelty detection since last timestamp
- Ranking improvements from implicit feedback
- Context preservation (project states, recurring routines)

---

**→ See [implementation_spec.md](./implementation_spec.md) for:**
- Complete database schema (Postgres tables)
- Full orchestrator pipeline details
- Agent runtime specifications
- UI design requirements
- Implementation phases & checklist
- Acceptance tests
