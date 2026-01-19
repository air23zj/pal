# Morning Brief AGI — Product One-Pager

> **For full implementation details, see [implementation_spec.md](./implementation_spec.md)**

## What it is

**Morning Brief** is an AI-native daily briefing web app that acts as your personal chief of staff—automatically gathering, filtering, and presenting only what matters from across your digital life, personalized through continuous learning.

## The Problem

Modern professionals drown in information scattered across 10+ platforms. Existing solutions either:
- Aggregate everything (creating noise)
- Rely on manual filtering (defeating the purpose)
- Don't understand what "new and important" means *to you*

## The Solution

Morning Brief combines:
- **Agentic browsing** for social and web sources
- **Deep integrations** via MCP with Google workspace
- **Persistent memory** to power novelty + personalization
- A **single beautiful dashboard** each morning containing only signal—no noise

## Core Differentiator

**Context-aware personalization** through a sophisticated memory system that:
- Learns your priorities
- Tracks what you've seen
- Understands temporal relevance
- Evolves its judgment through interaction

## Dashboard Modules

Each module shows **"New since last brief"** + **importance-ranked highlights**:

- **News** — top events aligned to your interests + "why this matters"
- **Social (X/LinkedIn)** — meaningful updates from tracked people/topics
- **Research Radar** — new papers, threads, breakthroughs (arXiv, social)
- **Podcasts** — new episodes + "should you listen?" summaries
- **Project Status** — changes, blockers, next actions
- **Calendar** — today's schedule + prep notes + risks + travel buffers
- **Commute** — ETA, delays, suggested departure time
- **Exercise** — goal progress + suggested plan
- **Weather** — what impacts your day (rain windows, temperature swings)
- **Family** — activities, reminders, logistics
- **Inbox Delta** — "only emails that matter" + action suggestions
- **Todos/Notes** — resurfaced tasks from Keep/Tasks based on today's context

## "Only Important & New" — The Core Promise

**Three Personalized Gates:**

### A) Novelty Filter
- Deduplicate against what you've already seen
- Track "last read / last summarized"
- Detect "new developments" vs reposts/repeats

### B) Importance Ranking
- Impact on deadlines, relationships, money, health, projects
- Source credibility + proximity to you (team, family, VIPs)
- Relevance to your active goals

### C) Actionability
- Does this require action today?
- Is there a decision to make?
- Is this a risk if ignored?

## Typical Daily Flow (60 seconds)

1. Open Morning Brief
2. See top 5 "Today matters" items
3. Scan modules (news/social/research/schedule/commute)
4. Click into 1–2 items for evidence
5. One-tap actions: reply, add task, block time, bookmark, follow-up

## Success Metrics

- **Time-to-brief:** < 2 minutes/day
- **"Repeat content" rate:** < 10%
- **Actions taken:** tasks created, emails replied, meetings prepped
- **Weekly retention:** 5+ days/week usage
- **"I missed something important"** incidents → zero

## Privacy & Trust

- You control connected accounts
- Structured memory storage, not raw personal data by default
- Audit log: "why this was shown"
- Sandboxed browsing & tool execution

---

**→ See [implementation_spec.md](./implementation_spec.md) for full technical details**
