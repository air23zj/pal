# Morning Brief AGI — Complete Implementation Spec

**Purpose:** Complete implementation specification combining product vision, architecture design, and engineering contracts  
**Version:** 1.0  
**Scope:** MVP → V1 implementation-ready  
**Core Thesis:** Memory-driven novelty detection + personalized importance ranking is the moat

> **Quick References:** See [product.md](./product.md) for product overview, [arch.md](./arch.md) for architecture summary, [spec.md](./spec.md) for technical contracts quick reference

---

## 1) Vision

Morning Brief AGI is an intelligent morning briefing system that acts as your personal chief of staff—automatically gathering, filtering, and presenting only what matters from across your digital life, personalized through continuous learning about your priorities and interests.

**Core Differentiator:** Context-aware personalization through a sophisticated memory system that learns your priorities, tracks what you’ve seen, and understands temporal relevance.

---

## 2) Problem

Modern professionals drown in information scattered across 10+ platforms. Existing solutions either aggregate everything (creating noise) or rely on manual filtering (defeating the purpose). You need an AI that truly understands what “new and important” means *to you*, evolving its judgment through interaction.

---

## 3) Solution Overview

Morning Brief AGI combines:

* **Agentic browsing** for social and web sources
* **Deep integrations** via MCP with Google workspace
* **Persistent memory** to power novelty + personalization
* A **single beautiful dashboard** each morning containing only signal—no noise

---

## 4) MVP Features (Weeks 1–4)

✅ Required in MVP:

* Beautiful responsive dashboard, card-based
* MCP: Google Calendar + Gmail + Tasks (Keep optional)
* News aggregation from configured RSS feeds
* Basic memory system: seen content tracking + last check timestamps
* Manual refresh + scheduled generation at 6 AM local time
* User preference configuration UI (topics + sources + verbosity)
* Feedback controls: 👍 / 👎 / Dismiss / Mark seen / Save / Less like this

---

## 5) V1 Features (Weeks 5–8)

✅ Add in V1:

* X (Twitter) and LinkedIn agents via **browser-use**
* arXiv monitoring with keyword/topic matching
* Podcast tracking (Spotify/Apple podcasts APIs, RSS fallback)
* Advanced memory: interaction learning + relevance ranking
* Weather + commute intelligence
* Project status tracking from connected tools (optional stub)

---

## 6) System Architecture

### 6.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend Dashboard                      │
│  Next.js + Tailwind + shadcn/ui + Framer + Recharts     │
└───────────────────┬─────────────────────────────────────┘
                    │ WebSocket + REST API
┌───────────────────┴─────────────────────────────────────┐
│             Orchestration Layer (FastAPI)                │
│  - Pipeline coordinator - Memory manager - Task queue    │
└───────────────┬──────────────────┬──────────────────────┘
                │                  │
        ┌───────┴────────┐    ┌────┴─────────┐
        │  Agent Sandbox │    │ MCP Servers  │
        │  (E2B/Firebase)|    │ (Google APIs)│
        │  - Browser-Use │    │ - Gmail      │
        │  - Playwright  │    │ - Calendar   │
        │  - Claude API  │    │ - Keep/Tasks │
        └────────┬────────┘    └──────────────┘
                 │
        ┌────────┴─────────┐
        │  Memory System   │
        │  PostgreSQL +    │
        │  Vector DB (V1)  │
        │  Filesystem      │
        └──────────────────┘
```

> Note: MVP can ship without Vector DB; V1 adds Qdrant.

---

## 7) Repo Layout (Codex MUST follow)

```
morning-brief/
  apps/
    web/                          # Next.js dashboard
    api/                          # FastAPI backend
    orchestrator/                 # Pipeline orchestration + Celery tasks
  packages/
    shared/                       # shared types + schemas
    connectors/                   # MCP connectors wrapper
    agent_runtime/                # E2B/Firecracker abstraction
    memory/                       # filesystem memory manager
    ranking/                      # novelty + importance scoring
    editor/                       # brief synthesis + formatting
  infra/
    docker/                       # docker-compose local dev
    migrations/                   # alembic migrations
  docs/
    codex_implementation_spec.md  # this file
```

---

## 8) Tech Stack (Locked)

### Frontend

* Next.js 14 (App Router), React 18, TypeScript
* Tailwind CSS + shadcn/ui
* Framer Motion
* Recharts
* WebSocket updates + REST fallback

### Backend

* FastAPI (Python 3.11+)
* Celery + Redis task queue
* Custom pipeline orchestration
* MCP clients for Google services

### Agents & Runtime

* browser-use (headless browsing)
* Playwright (fallback; optional)
* **Sandboxing options:**
  * Cloud: E2B, Firecracker
  * Local: **open-skills** ([github.com/instavm/open-skills](https://github.com/instavm/open-skills))
* **LLM options:**
  * Cloud: Claude, Gemini, OpenAI
  * Local: Ollama, LM Studio

### Storage & Infra

* Postgres (structured truth)
* File system memory (agent working memory + logs)
* Qdrant (V1 embeddings)
* **Sandboxing:**
  * Cloud: E2B, Firecracker
  * Local: open-skills
* Docker Compose local dev
* Kubernetes later
* Cloudflare Workers edge caching later
* Supabase for auth + realtime later

---

## 9) Deployment Configurations

### 9.1 Cloud Deployment (Production)

**Characteristics:**
- Fast, managed infrastructure
- Auto-scaling capabilities
- Pay-per-use model
- External API dependencies

**Stack:**
```yaml
Sandbox: E2B or Firecracker
LLM: Claude (primary), Gemini (cost optimization), OpenAI (backup)
Database: Managed Postgres (AWS RDS / Supabase)
Cache: Redis (managed)
Hosting: Kubernetes / Cloud Run
```

**Pros:**
- Fastest time to production
- Minimal ops overhead
- Elastic scaling

**Cons:**
- Data processed by external APIs
- Recurring API costs
- Network dependency

### 9.2 Local Deployment (Privacy-First)

**Characteristics:**
- Complete data sovereignty
- Zero external API calls
- One-time hardware cost
- Requires local GPU for LLMs

**Stack:**
```yaml
Sandbox: open-skills (https://github.com/instavm/open-skills)
LLM: Ollama or LM Studio (local inference)
Database: Local Postgres
Cache: Local Redis
Hosting: Docker Compose
```

**Pros:**
- Complete privacy, zero data upload
- No recurring API costs
- No network dependency
- Full control

**Cons:**
- Requires capable hardware (16GB+ RAM, GPU recommended)
- More setup complexity
- Manual scaling

### 9.3 Hybrid Deployment (Recommended)

**Characteristics:**
- Use cloud for non-sensitive data
- Use local for private data
- Optimize for cost and privacy

**Example:**
```yaml
Sandbox: open-skills (local)
LLM: Claude for synthesis + Ollama for classification
Database: Local Postgres
MCP: Direct Google API calls (OAuth, no proxy)
```

### 9.4 Configuration Management

**Environment Variables:**
```bash
# Runtime
SANDBOX_PROVIDER=open-skills  # open-skills | e2b | firecracker
SANDBOX_ENDPOINT=http://localhost:8222  # for open-skills

# LLM
LLM_PROVIDER=claude  # claude | gemini | openai | ollama | lmstudio
LLM_ENDPOINT=https://api.anthropic.com
LLM_MODEL=claude-sonnet-4
LLM_API_KEY=sk-xxx

# Fallback LLM (optional)
LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_ENDPOINT=http://localhost:11434
LLM_FALLBACK_MODEL=llama3.2

# Database
DATABASE_URL=postgresql://localhost/morning_brief

# MCP Servers
MCP_GMAIL_ENABLED=true
MCP_CALENDAR_ENABLED=true
MCP_TASKS_ENABLED=true
```

---

## 10) Data Contracts (Strict)

**All modules MUST return the same shape to UI.**

### 9.1 BriefBundle (Backend → UI)

```json
{
  "brief_id": "brief_2026-01-18T06:03:00-08:00",
  "user_id": "u_123",
  "timezone": "America/Los_Angeles",
  "brief_date_local": "2026-01-18",
  "generated_at_utc": "2026-01-18T14:03:05Z",
  "since_timestamp_utc": "2026-01-17T14:00:00Z",

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

### 9.2 ModuleResult (uniform contract)

```json
{
  "status": "ok",
  "summary": "2 important updates; 1 requires action today.",
  "new_count": 3,
  "updated_count": 1,
  "items": [ /* BriefItem[] */ ]
}
```

Allowed status values:

* `ok | degraded | error | skipped`

### 9.3 BriefItem (uniform across sources)

```json
{
  "item_ref": "item_arxiv_2401.12345",
  "source": "arxiv",
  "type": "paper",
  "timestamp_utc": "2026-01-18T04:21:00Z",

  "title": "Tool-Augmented Agents with Filesystem Memory",
  "summary": "Proposes a filesystem-based memory layout enabling reliable tool use.",
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
    {"type": "bookmark", "label": "Save to reading list"},
    {"type": "add_task", "label": "Review and extract insights"}
  ]
}
```

### 9.4 Action

```json
{
  "action_id": "act_01",
  "type": "create_task",
  "label": "Add task: Review paper",
  "payload": {
    "title": "Review arXiv 2401.12345",
    "due_date_local": "2026-01-18",
    "source_item_ref": "item_arxiv_2401.12345"
  }
}
```

---

## 11) Database Schema (Postgres Source of Truth)

### 10.1 Tables

**users**

* id (pk)
* created_at
* timezone
* settings_json
* importance_weights_json
* last_brief_timestamp_utc

**brief_runs**

* id (pk)
* user_id (fk)
* status (queued|running|ok|degraded|error)
* since_timestamp_utc
* generated_at_utc
* latency_ms
* cost_estimate_usd
* warnings_json

**brief_bundles**

* id (pk) = brief_id
* user_id (fk)
* brief_date_local
* generated_at_utc
* bundle_json

**items**

* id (pk) (stable hash)
* user_id (fk)
* source
* type
* source_id
* timestamp_utc
* title
* summary
* entity_keys_json
* url
* created_at

**item_states**

* user_id
* item_id
* state (new|updated|seen|ignored|saved)
* first_seen_utc
* last_seen_utc
* opened_count
* saved_bool
* feedback_score

PK(user_id, item_id)

**feedback_events**

* id (pk)
* user_id
* item_id
* event_type (thumb_up|thumb_down|dismiss|less_like_this|mark_seen|save|open)
* created_at_utc
* payload_json

---

## 12) Filesystem Memory (Moat)

Filesystem is for **agent personalization + novelty tracking + debuggability**.
DB remains truth for durable states.

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

### 11.1 Memory responsibilities

* Deduplication (never show twice)
* Novelty detection since last timestamp
* Ranking improvements from implicit feedback
* Context preservation (project states, recurring routines)

---

## 13) Orchestrator Pipeline (Custom DAG)

### 13.1 Stages (MVP)

**Node 0 — LoadContext**

* Load user profile: DB + filesystem
* Determine `since_timestamp_utc` (from users table or fallback 24h)

**Node 1 — GatherCandidates (parallel)**

* Gmail delta (MCP)
* Calendar (today + tomorrow) (MCP)
* Tasks + Keep (MCP)
* News agent (RSS/API)
* Research (arXiv RSS/API)
* Weather (API or stub)
* Commute (API or stub)

**Node 2 — NormalizeCandidates**

* Transform candidates → canonical `items` format
* Extract entities + topics

**Node 3 — NoveltyFilter**

* Exact dedupe: source_id exists & seen recently
* Update detection: entity overlap + new timestamp + delta > threshold
* Label each item: NEW / UPDATED / REPEAT / LOW_SIGNAL

**Node 4 — RankImportance**
Compute scores per item:

* relevance / urgency / credibility / actionability / final_score

**Node 5 — SelectAndCap**

* highlights max 5
* module caps 3–8
* total items cap 30

**Node 6 — BriefSynthesis (Claude)**

* Add `why_it_matters`
* Produce per-module summaries
* Generate suggested actions

**Node 7 — Persist**

* Store bundle_json
* Upsert items
* Update item_states
* Update filesystem memory timestamps + seen fingerprints
* Update users.last_brief_timestamp_utc

**Node 8 — Done**
Return brief_id + status

### 13.2 V1 nodes (added)

* Social X ingestion via browser-use agent
* Social LinkedIn via browser-use agent
* Podcasts ingestion
* Embeddings + Qdrant semantic dedupe

---

## 14) Novelty & Ranking Spec (Non-Negotiable)

### 14.1 Stable item IDs

Compute:

* `stable_id = hash(source + type + source_id)`
  Fallback:
* `hash(url + timestamp_bucket + title)`

### 14.2 Novelty rules (MVP)

* If exact source_id exists in items and item_state seen within 14 days → `REPEAT`
* Else if entity overlap matches and timestamp newer and delta score > threshold → `UPDATED`
* Else → `NEW`

Only show:

* NEW
* UPDATED (if meaningful)

### 14.3 Ranking formula (MVP)

```
final_score =
  0.45 * relevance +
  0.20 * urgency +
  0.15 * credibility +
  0.10 * impact_proxy +
  0.10 * actionability
```

Feature definitions:

* relevance: topic weights + VIP mentions + project tags
* urgency: meetings/todos due within 24h
* credibility: trusted source weights (gmail/calendar/arxiv higher)
* impact_proxy: mentions your core entities (projects/people)
* actionability: requires response / has next-step

### 14.4 Caps & budgets

* highlights <= 5
* module default view <= 3 items (expand optional)
* module max <= 8 items
* total <= 30 items

---

## 15) Agent Runtime (Sandboxed — Cloud & Local Options)

### 15.1 Runtime Architecture

Agents run in isolated sandboxes with support for both cloud and local deployment:

**Cloud Options:**
* **E2B** - Serverless sandboxes, fastest cloud setup
* **Firecracker** - VM-level isolation, production-grade security

**Local Options:**
* **open-skills** - Local MCP server with VM-level isolation ([github.com/instavm/open-skills](https://github.com/instavm/open-skills))
  * Docker container isolation with Apple Container technology
  * Built-in skills system compatible with Claude's official skills
  * Integrated browser automation (Playwright)
  * Jupyter kernel for Python execution
  * Zero data upload - fully local execution
  * MCP server interface for tool communication

**Interface (abstract):**

```python
# Unified interface regardless of runtime
Sandbox.run(
    agent_name: str,
    input_json: dict,
    mounts: list,
    network_policy: dict
) -> output_json
```

**open-skills MCP Tools:**
```python
# Available when using open-skills runtime
- execute_python_code(code: str) -> result
- list_skills() -> available_skills
- get_skill_info(skill_name: str) -> documentation
- get_skill_file(skill_name: str, path: str) -> content
- navigate_and_get_all_visible_text(url: str) -> scraped_content
```

**File Mapping (open-skills):**
- Host: `~/.open-skills/assets/outputs` → Container: `/app/uploads`
- Skills: `~/.open-skills/assets/skills/` → Container: `/app/skills`

### 15.2 LLM Options

**Cloud APIs:**
* **Claude** (Anthropic) - Primary for synthesis & reasoning
* **Gemini** (Google) - Alternative for cost optimization
* **OpenAI** (GPT-4) - Backup option

**Local Models:**
* **Ollama** - Local model serving, privacy-first
* **LM Studio** - Alternative local inference

**Configuration:**
```python
# LLM provider config (environment or config file)
LLM_PROVIDER = "claude"  # claude | gemini | openai | ollama | lmstudio
LLM_ENDPOINT = "https://api.anthropic.com"  # or local: http://localhost:11434
LLM_MODEL = "claude-sonnet-4"
```

### 15.3 Agent list (MVP → V1)

MVP:

* news_agent
* research_agent_arxiv
* inbox_agent (MCP wrapper)
* calendar_agent (MCP wrapper)
* brief_editor_agent

V1:

* social_agent_x (browser-use)
* social_agent_linkedin (browser-use)
* podcasts_agent

### 15.4 Read-only enforcement

Agents MUST NOT post/like/comment/reply.
Runtime MUST enforce:

* no form submissions
* no click on "post"
* no write APIs

**Enforcement (open-skills):**
- Network policy: block POST/PUT/DELETE to social platforms
- Browser automation: disable form submissions
- Container mounts: read-only where possible

---

## 16) Backend API Spec (FastAPI)

### Required endpoints

**GET /api/brief/latest**
Returns latest stored BriefBundle (cached).

**POST /api/brief/run**
Triggers orchestration run (async). Returns run_id.

**GET /api/brief/run/{run_id}**
Returns run status + metadata.

**GET /api/brief/{brief_id}**
Returns bundle JSON.

**POST /api/feedback**
Body:

```json
{
  "item_ref": "item_x_123",
  "event_type": "thumb_down",
  "payload": { "reason": "not important" }
}
```

**POST /api/item/mark_seen**
Marks seen immediately.

---

## 17) UI Design Requirements (Ship-level)

### Design philosophy

“Calm intelligence at a glance”

### UI rules

* Always show top-level weather + commute + quick counts
* Always show why_it_matters for every item
* Priority indicators: critical/important/fyi
* Great empty states: “All caught up”
* Accessibility: WCAG 2.1 AA
* Reduced motion supported

### Dashboard layout

Follow your design one-pager layout and component states.

---

## 18) Scheduling

* Scheduled morning generation at **6:00 AM local**
* Manual refresh button triggers async run
* UI loads cached latest instantly, then updates when run completes

Implementation:

* Celery beat for schedule
* Redis for job state

---

## 19) Observability & Audit

For each brief run store:

* latency
* cost estimate
* modules degraded
* per-agent stats
* score breakdown per item (“why shown”)

---

## 20) Security Requirements

* OAuth 2.0 for integrations
* Credentials encrypted at rest
* **Sandbox isolation:**
  * Cloud: VM-level isolation (E2B/Firecracker)
  * Local: Container isolation with VM properties (open-skills)
* Rate limiting + cost caps
* Network policies: block write APIs for read-only agents
* **Privacy options:**
  * Cloud deployment: data processed via external APIs
  * Local deployment: zero data upload, fully local execution
* Human-in-loop required for any write actions (future)

---

## 21) Implementation Phases (Codex Checklist)

### Phase 1 — Skeleton + contracts

* [ ] repo layout
* [ ] shared schemas
* [ ] stub BriefBundle
* [ ] basic dashboard rendering

### Phase 2 — DB + persistence

* [ ] migrations
* [ ] store/read brief_bundles
* [ ] feedback_events & item_states

### Phase 3 — MCP connectors

* [ ] Gmail delta
* [ ] Calendar events
* [ ] Tasks/Keep
* [ ] normalize items

### Phase 4 — Memory + novelty

* [ ] filesystem memory manager
* [ ] seen-fingerprints
* [ ] novelty labeling

### Phase 5 — Ranking + selection

* [ ] implement scoring
* [ ] caps enforcement
* [ ] top highlights generation

### Phase 6 — Brief synthesis agent

* [ ] Claude editor prompt & output enforcement
* [ ] why_it_matters generation
* [ ] module summaries

### Phase 7 — V1 social agents

* [ ] Runtime setup (choose: E2B/Firecracker cloud or open-skills local)
* [ ] LLM provider configuration (cloud or local)
* [ ] browser-use X agent
* [ ] browser-use LinkedIn agent
* [ ] open-skills custom skills (if using local runtime)

### Phase 8 — polish

* [ ] WebSocket updates
* [ ] deep dive item page
* [ ] “less like this” changes weights

---

## 22) Definition of Done (MVP)

* Daily brief produces only NEW/UPDATED items
* Dashboard loads instantly from cached latest
* Partial failures degrade per module without breaking UI
* Every card has why_it_matters + evidence
* Feedback updates future importance weighting
* Memory prevents repeats across days

---

## 23) Acceptance Tests (Automatable)

### Unit tests

* stable hash ID generation
* novelty: repeat detection
* updated detection
* ranking boosts VIP mentions

### Integration tests

* orchestrator run generates valid bundle schema
* module caps enforced
* degraded module doesn’t fail bundle

### E2E tests

* open dashboard loads latest brief
* trigger run updates brief_id
* feedback event persists and affects ranking weight

---

# End of Spec

---