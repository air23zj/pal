# Morning Brief AGI — Architecture Quick Reference

> **For full implementation details, see [implementation_spec.md](./implementation_spec.md)**

## High-Level Architecture

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
        │  Cloud: E2B/   │    │ (Google APIs)│
        │    Firecracker │    │ - Gmail      │
        │  Local: open-  │    │ - Calendar   │
        │    skills MCP  │    │ - Keep/Tasks │
        └────────┬────────┘    └──────────────┘
                 │
        ┌────────┴─────────┐
        │  Memory System   │
        │  PostgreSQL +    │
        │  Vector DB (V1)  │
        │  Filesystem      │
        └──────────────────┘
```

## Core Components

### Frontend Dashboard
**Purpose:** Fast scanning, minimal clutter, transparency

**Key Screens:**
- **Today Brief (default)**: top priority items + modules
- **Deep Dive**: expanded thread/paper/email summaries
- **Settings**: topics, sources, importance tuning
- **Feedback**: "show less / show more / seen / ignore source"

### Orchestrator (Briefing Planner)
**Purpose:** Decide what to fetch, how deep, when to stop

**Responsibilities:**
- Schedule daily run (6 AM local) + on-demand refresh
- Call connectors/agents in parallel
- Enforce budgets (time + token + cost)
- Assemble final brief JSON

### Data Acquisition Layer

**1) Native Connectors (MCP/APIs)**
- Gmail, Google Calendar, Chat, Tasks/Keep

**2) Agentic Browsing (browser-use + sandbox)**
- X.com, LinkedIn, Research threads, Podcasts

**Design Principle:** Use APIs where possible; use agents where necessary.

### Agent Runtime (Sandboxed — Cloud & Local)

**Cloud Options:**
- **E2B** - Serverless sandboxes, fastest setup
- **Firecracker** - VM-level isolation, production-grade

**Local Option:**
- **open-skills** ([github.com/instavm/open-skills](https://github.com/instavm/open-skills))
  - MCP server with VM-level container isolation
  - Skills system (compatible with Claude's official skills)
  - Browser automation (Playwright)
  - Python execution (Jupyter kernel)
  - Zero data upload, fully local

**LLMs:**
- **Cloud:** Claude, Gemini, OpenAI
- **Local:** Ollama, LM Studio

**Specialized workers + orchestrator approach**

Agents:
- `social_agent_x` / `social_agent_linkedin`
- `research_agent_arxiv`
- `news_agent`
- `inbox_delta_agent`
- `calendar_agent`
- `life_ops_agent` (weather/commute/fitness/family)
- `brief_editor_agent` (final synthesis)

### Memory System
**Purpose:** Answer "Is this new?" and "What's important to me?"

**Structure:**
```
/memory/
  profile/          # preferences, topics, importance rules
  state/            # last_brief_timestamp, read_receipts
  entities/         # people, orgs, projects
  episodes/         # daily brief history
  embeddings/       # semantic search (V1)
  feedback/         # interaction logs
```

**Two-Tier:**
- **STM (7–14 days)**: novelty detection + continuity
- **LTM (persistent)**: stable preferences, learned patterns

### Novelty Engine
**Labels:** `NEW` | `UPDATED` | `REPEAT` | `LOW_SIGNAL`

**Checks:**
- Exact match: URL hash, message-id, arxiv-id
- Semantic match: embedding similarity
- Update match: same entities + new timestamp + meaningful delta

### Importance Ranking
**Score = relevance + urgency + credibility + impact + actionability**

Initial: heuristic features → weighted sum  
Evolution: preference learning from feedback

### Brief Synthesis
`brief_editor_agent` produces:
- Final brief sections
- "Why it matters" per highlight
- 1-click actions (reply, task, calendar, bookmark)
- Citations/evidence links

## Guardrails & Budgets

**Hard Constraints:**
- Time budget per module: 5–15s
- Total items shown cap: 30
- Maximum deep dives per run: 3

**Safety:**
- Agents are read-only by default
- Explicit user approval for write actions
- Sandbox network constraints

## Implementation Phases

**Phase 1 — "Signal wins" MVP**
- Gmail + Calendar + Weather + Commute
- News + arXiv topics
- Memory: last_brief + dedupe + read receipts
- Basic ranking + UI dashboard

**Phase 2 — Social agent browsing**
- X + LinkedIn agent ingestion (read-only)
- Novelty detection across social feeds

**Phase 3 — Learning personalization**
- Feedback loop training
- Automatic importance tuning

**Phase 4 — Executive assistant behaviors**
- Auto-draft replies
- Meeting prep packs
- Proactive agenda recommendations

---

**→ See [implementation_spec.md](./implementation_spec.md) for detailed schemas, DB design, and build checklist**
