# Morning Brief AGI — Use Cases

**File:** `docs/use_case.md`  
**Status:** Draft v1.0  
**Scope:** MVP + V1 (social agents) with forward notes for V2

---

## 1) Purpose

This document defines the **user-facing use cases** for Morning Brief AGI: the actions a user takes, the system behaviors expected, and the acceptance criteria that make the product “feel right” (high-signal, personalized, and trustworthy).

Morning Brief is not a feed reader. It is a **delta-aware, memory-driven chief-of-staff** that shows **only what’s new and important** since the last brief.

---

## 2) Personas

### 2.1 Primary persona: Power user / builder / researcher
- Heavy information intake: X, LinkedIn, arXiv, podcasts, email, calendar
- Wants: *signal extraction*, trend awareness, and project continuity
- Low tolerance for repeats and fluff

### 2.2 Secondary persona: Exec / manager
- Wants: meetings prep, VIP messages, urgent risks/opportunities
- Needs trust: evidence, “why shown”, and minimal hallucination

### 2.3 Tertiary persona: Family coordinator
- Wants: logistics, shared calendar, reminders, time-sensitive alerts
- Needs privacy controls and gentle UX

---

## 3) Key Definitions

- **Brief**: A generated dashboard snapshot for a time window.
- **Episode**: A single run of the pipeline (same as a Brief generation run).
- **Module**: A section of the dashboard (News, Inbox, Calendar, etc.).
- **Item**: A single surfaced unit (email, post, paper, event, task).
- **Novelty label**: `NEW | UPDATED | REPEAT | LOW_SIGNAL`
- **Importance score**: Ranking score used for selection and highlight promotion.
- **Evidence**: URLs/snippets explaining provenance (required for trust).
- **Memory (brain-inspired)**:
  - **Hippocampus**: episodic ledger (what happened, what was shown, what user did)
  - **Neocortex**: semantic preferences (topics, VIPs, source trust)
  - **PFC**: gating/policy (budgets, write rules, selection)
  - **Amygdala**: salience tags (urgency, risk, personal significance)

---

## 4) Guiding Principles (Product Invariants)

1. **No repeats**: Don’t show the same thing twice unless it meaningfully changed.
2. **Explainability**: Every surfaced item must have:
   - evidence (URL/snippet)
   - “why it matters”
   - “why shown” factors (topic match / VIP / urgency / etc.)
3. **Personalized importance**: The ranking improves based on user behavior.
4. **Degraded-but-functional**: Missing integrations must not break the brief.
5. **Read-only by default**: Agents must not post/reply/modify accounts in MVP/V1.

---

## 5) Primary Daily Flow

### UC-01: Consume Morning Brief (Default)
**Trigger:** User opens the app in the morning.

**System behavior:**
- Loads **cached latest BriefBundle** instantly.
- Displays:
  - Top Highlights (≤ 5)
  - Today timeline (calendar + commute + weather impact)
  - Work focus (inbox delta + tasks due)
  - Discovery (news + research + social + podcasts)
  - Life (exercise + family)

**Acceptance criteria:**
- Time-to-first-render < 2s (cached bundle).
- Total items shown ≤ 30, module items ≤ 8.
- Every item shows: title, summary, why-it-matters, novelty label, evidence link.
- Modules can be `ok | degraded | error | skipped` without breaking UI.

---

## 6) Core MVP Use Cases

### UC-02: Generate Brief on Schedule (6:00 AM Local)
**Trigger:** Scheduled job runs daily at 6:00 AM user timezone.

**System behavior:**
- Uses `since_timestamp` = last successful brief timestamp.
- Runs orchestrator pipeline with budgets/timeouts.
- Produces a BriefBundle even if some modules fail (degraded).
- Updates:
  - last_brief_timestamp
  - item states (seen/new/updated)
  - episodic memory logs

**Acceptance criteria:**
- A valid BriefBundle is stored every day (status `ok` or `degraded`).
- If run fails, last_brief_timestamp is not advanced.

---

### UC-03: Manual Refresh
**Trigger:** User clicks “Refresh” on dashboard.

**System behavior:**
- Enqueues a run with a strict runtime cap.
- UI continues showing cached brief until new one is ready.
- UI updates when new brief is available (polling or WebSocket).

**Acceptance criteria:**
- Refresh never blocks UI.
- New brief replaces old brief only after validation succeeds.

---

### UC-04: Deep Dive an Item
**Trigger:** User clicks an item.

**System behavior:**
- Shows expanded details:
  - evidence list (URLs/snippets)
  - why-it-matters (and optionally a longer explanation)
  - related items (same entity/topic cluster) if available
- Marks item as “opened” for learning signals.

**Acceptance criteria:**
- Deep dive page is deterministic and grounded in evidence (no invented facts).
- Opening an item updates item_state.opened_count.

---

### UC-05: Give Feedback (Train Personalization)
**Trigger:** User taps 👍 / 👎 / Dismiss / Save / Less like this / Mark seen.

**System behavior:**
- Writes feedback_event to DB and mirrors to memory logs.
- Updates item_state (seen/saved/ignored/feedback score).
- Applies minimal personalization changes:
  - Upweight topics/entities for saves/opens/thumbs-up
  - Downweight for dismiss/less-like-this/thumbs-down
- Changes affect future ranking.

**Acceptance criteria:**
- Feedback is reflected in ranking within 1–3 runs.
- “Less like this” reduces similar items (topic/source/entity) noticeably.

---

### UC-06: Configure Preferences (Topics, Sources, Brief Style)
**Trigger:** User opens Settings and changes preferences.

**System behavior:**
- Allows user to set:
  - interest topics + weights (coarse)
  - VIP people list
  - source toggles (enable/disable modules)
  - brief verbosity (tight/medium)
  - schedule time (MVP may keep 6 AM fixed; store anyway)
- Updates semantic memory (Neocortex) and DB settings_json.

**Acceptance criteria:**
- Disabling a source removes its module or marks `skipped`.
- Changing verbosity changes summary length in the next brief.

---

### UC-07: Integration Setup (Google via MCP)
**Trigger:** User connects Google account via OAuth (or config) to enable MCP.

**System behavior:**
- Successfully connected → modules switch from degraded to ok.
- Missing/expired tokens → module remains degraded with a clear UI message.

**Acceptance criteria:**
- System remains functional without integrations.
- Degraded modules show: what’s missing + how to fix.

---

## 7) “Only New & Important” Use Cases (Novelty + Ranking)

### UC-08: Deduplicate Repeated Content
**Trigger:** Same email/thread/post appears again.

**System behavior:**
- Labels as `REPEAT` and does not show it by default.
- If content changed significantly (delta), label as `UPDATED`.

**Acceptance criteria:**
- After two consecutive daily runs, repeat rate < 10% of surfaced items.
- `UPDATED` only when there is meaningful new information.

---

### UC-09: Promote Meaningful Updates
**Trigger:** A topic cluster has new key facts (e.g., paper revision, new thread update, calendar change).

**System behavior:**
- Shows as `UPDATED` with a concise “what changed” statement.
- Bubbles up to Top Highlights if:
  - urgent OR VIP OR high relevance OR action required

**Acceptance criteria:**
- Users can tell why it’s new vs yesterday in one glance.

---

### UC-10: Continuity / Open Loops
**Trigger:** Item requires action (reply needed, meeting soon, task due).

**System behavior:**
- Adds salience tags (urgency).
- Surfaces in Work Focus or Top Highlights.
- Suggests actions (e.g., “reply”, “create task”, “block time”).

**Acceptance criteria:**
- Action-required items are rarely missed (goal: >95% surfaced).

---

## 8) Reliability & Degraded Mode Use Cases

### UC-11: Source Failure / Rate Limits
**Trigger:** Google API down, MCP server unavailable, RSS fails.

**System behavior:**
- Module returns `degraded` with reason.
- Brief still generated with other modules.

**Acceptance criteria:**
- No brief generation failures due to a single module failure.
- UI clearly indicates degraded modules.

---

### UC-12: Cost/Time Budget Enforcement
**Trigger:** Run exceeds time or token budgets.

**System behavior:**
- PFC gating truncates:
  - fewer items per module
  - skips expensive modules
  - stops after cap
- Marks run as `degraded` if necessary.

**Acceptance criteria:**
- Runs terminate within hard cap (e.g., 60 seconds MVP).
- Output is still valid and useful.

---

## 9) Trust & Privacy Use Cases

### UC-13: Explain “Why Shown”
**Trigger:** User taps “Why am I seeing this?”

**System behavior:**
- Shows factors:
  - topic match
  - VIP mention
  - urgency (deadline/meeting)
  - new since last brief
  - source trust level

**Acceptance criteria:**
- Explanation is concise and evidence-aligned.

---

### UC-14: Forget / Remove Memory (User Control)
**Trigger:** User requests:
- “Forget this person/topic”
- “Delete my history”
- “Don’t track this”

**System behavior:**
- Deletes or deactivates:
  - item_states
  - topic/entity weights
  - selected memory logs (as per policy)
- Provides confirmation in UI.

**Acceptance criteria:**
- Future briefs respect the removal.
- Sensitive memory writes require explicit consent if enabled later.

---

## 10) V1 Use Cases (Social Agents via browser-use)

### UC-15: Scan X/LinkedIn for Relevant Updates (Read-only)
**Trigger:** Scheduled or manual run.

**System behavior:**
- Sandbox agent scrolls feed/notifications.
- Extracts candidate posts matching:
  - topics
  - VIP people
  - high engagement signals (optional)
- Enforces read-only rules:
  - no posting/liking/commenting
  - no form submissions

**Acceptance criteria:**
- Works without breaking accounts.
- Fails gracefully if login required or UI changes.

---

## 11) V2 Use Cases (Forward Notes)

- Natural language query: “Show me research on agent memory”
- Weekly/monthly digest with trend analysis
- Proactive notifications for time-sensitive items
- Family coordination (shared calendars, location-based triggers)
- Multi-modal: embedded audio clips, images, video previews

---

## 12) Non-Functional Requirements (MVP Targets)

- **Latency**: dashboard load <2s (cached), run <60s (degraded allowed)
- **Signal**: repeat content rate <10% after two days
- **Efficiency**: brief consumable in <3 minutes
- **Stability**: module failures do not break brief generation
- **Security**: read-only by default; sandbox isolation; no secret leakage
- **Accessibility**: WCAG 2.1 AA, reduced-motion supported

---

## 13) Edge Cases & Handling

- **Timezone/DST shifts**: always store timestamps in UTC, compute local boundaries at display time.
- **Multiple runs/day**: last_brief_timestamp updates only on success; track per-run since_timestamp.
- **Same story across sources**: dedupe clusters; keep highest credibility + best summary.
- **Calendar changes**: treat time changes within 24h as high salience.
- **RSS flakiness**: retry with backoff; degrade if still failing.
- **Long threads / paywalls**: store evidence URL + partial snippet; avoid scraping full content.
- **User disables a module**: module becomes `skipped` (not `error`).
- **No integrations connected**: brief still shows News/Research stubs and empty-state UX.

---

## 14) Open Questions (Decide Later)

- How aggressive should “updated” be (threshold)?
- Should “dismiss” apply to topic, source, or entity by default?
- Do we store partial text snippets for evidence (privacy tradeoff)?
- How to represent “project status” reliably (sources, tools)?

---
