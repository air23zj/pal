# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Morning Brief AGI is an intelligent briefing system that gathers data from multiple sources (Gmail, Calendar, Tasks, Twitter, LinkedIn), filters for novelty, ranks by importance, and synthesizes personalized daily briefs using LLMs.

## Build & Run Commands

```bash
# Install dependencies
make install              # Installs backend (pip) + frontend (npm)

# Development
make dev                  # Runs backend (uvicorn :8000) + frontend (next :3000) concurrently
make dev-backend          # Backend only
make dev-frontend         # Frontend only

# Docker
make up                   # Start all services (postgres, redis, backend, frontend)
make down                 # Stop services
make logs                 # View logs

# Code quality
make format               # Black (Python) + Prettier (TS)
make lint                 # Ruff (Python) + ESLint (TS)

# Database
make db-init              # Initialize database with seed data
make db-upgrade           # Apply Alembic migrations
make db-migrate           # Create new migration (prompts for message)
```

## Testing

```bash
# Run all tests
make test                 # Backend + frontend
make test-backend         # Backend only (pytest)

# Run specific test file
pytest tests/test_normalizer_comprehensive.py -v

# Run single test
pytest tests/test_core_functionality.py::TestNormalizer::test_normalize_social_post -v

# Run tests matching pattern
pytest -k "ranking" -v

# Coverage report
pytest --cov=backend/packages --cov-report=html
open htmlcov/index.html

# Run with markers
pytest -m unit            # Unit tests only
pytest -m integration     # Integration tests only
```

Tests use SQLite in-memory database (no setup needed). Fixtures are defined in `tests/conftest.py`.

## Architecture

```
Frontend (Next.js 14) → REST API → Backend (FastAPI)
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
       Connectors                    Agents                    Processing
    (Gmail, Calendar,         (Twitter, LinkedIn           (Normalizer →
     Tasks via MCP)            via Playwright)              Memory →
            │                           │                    Ranking →
            └───────────────────────────┴───────────────────────────┘
                                        │
                              BriefOrchestrator
                                        │
                              LLM Synthesis (Claude/OpenAI/Ollama)
                                        │
                              BriefBundle → PostgreSQL
```

**Data flow:**
1. **Connectors/Agents** fetch raw data from sources
2. **Normalizer** converts all sources to uniform `BriefItem` format
3. **Memory** detects novelty (NEW/UPDATED/REPEAT) via fingerprinting
4. **Ranker** scores items: `0.45*relevance + 0.20*urgency + 0.15*credibility + 0.10*actionability + 0.10*impact`
5. **Editor** uses LLM to generate "why_it_matters" explanations
6. **Orchestrator** coordinates the pipeline and returns `BriefBundle`

## Key Directories

- `backend/apps/api/` - FastAPI routers (brief, feedback, health)
- `backend/packages/` - Business logic modules:
  - `shared/schemas.py` - Pydantic data contracts (BriefItem, BriefBundle, etc.)
  - `database/` - SQLAlchemy models + CRUD operations
  - `connectors/` - Gmail, Calendar, Tasks via MCP
  - `agents/` - Twitter, LinkedIn browser automation (Playwright)
  - `normalizer/` - Source → BriefItem conversion
  - `memory/` - Fingerprinting and novelty detection
  - `ranking/` - Multi-dimensional importance scoring
  - `editor/` - LLM client abstraction
  - `orchestrator/` - Pipeline coordinator
- `frontend/src/` - Next.js 14 app (App Router)
- `tests/` - Pytest test suite

## Data Contracts

**Critical:** Keep schemas in sync between:
- `backend/packages/shared/schemas.py` (Python/Pydantic)
- `frontend/src/types/brief.ts` (TypeScript)

When modifying schemas: update Python first, then TypeScript, then verify both sides.

## Code Style

- **Python:** Black + Ruff, 100-char line length
- **TypeScript:** Prettier + ESLint, Tailwind for styling
- **Commits:** Conventional format (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/brief/latest` - Get latest brief
- `POST /api/brief/run` - Trigger brief generation
- `POST /api/feedback` - Record user feedback (seen, dismiss, etc.)
- `GET /docs` - Swagger UI

## LLM Configuration

Set in `.env`:
```bash
LLM_PROVIDER=ollama       # or "claude" or "openai"
LLM_MODEL=llama3.2        # model name
ANTHROPIC_API_KEY=...     # if using Claude
OPENAI_API_KEY=...        # if using OpenAI
```

---

## AI Coding Workflow Guidelines (Empirical Notes, Dec 2025)

This section captures hard-won lessons from heavy agent-assisted development. These observations should guide both AI behavior and human-AI collaboration.

### Known Failure Modes (Watch Out For These)

Models make **subtle conceptual errors**, not syntax errors. The most common patterns:

1. **Wrong assumptions** - Making assumptions on your behalf and running with them without checking. Always surface assumptions explicitly.
2. **No confusion management** - Not seeking clarifications, not surfacing inconsistencies, not presenting tradeoffs, not pushing back when appropriate.
3. **Sycophancy** - Being too agreeable. Push back when something seems wrong or suboptimal.
4. **Over-engineering** - Overcomplicating code and APIs, bloating abstractions, adding unnecessary configurability.
5. **Code bloat** - Implementing 1000 lines when 100 would do. Always ask: "couldn't this be simpler?"
6. **Dead code accumulation** - Not cleaning up after refactoring. Remove what's no longer needed.
7. **Collateral changes** - Modifying/removing comments and code orthogonal to the task at hand.

### Effective Patterns (Do More Of These)

1. **Declarative over imperative** - Don't tell the AI what to do step-by-step. Give success criteria and let it loop until met. This creates leverage.
2. **Tests first** - Write tests first, then implement until they pass. This is where agent tenacity shines.
3. **Naive then optimize** - Write the naive algorithm that is very likely correct first, then optimize while preserving correctness.
4. **Plan mode for complex work** - Use plan mode for anything non-trivial. There's a need for lightweight inline planning too.
5. **Human as hawk** - Watch code changes carefully in an IDE. The AI handles generation; you handle discrimination (reviewing).
6. **Simplicity challenges** - When code feels bloated, ask "couldn't you just do X instead?" The AI will often immediately find a 10x simpler solution.

### The New Workflow Reality

- **80/20 flip**: Many engineers have gone from 80% manual coding to 80% agent coding in weeks.
- **Speedup vs expansion**: The main effect isn't just doing things faster—it's doing things that wouldn't have been worth coding before, and approaching code that was previously blocked by knowledge gaps.
- **Tenacity advantage**: Agents never get tired or demoralized. They'll work at something for 30 minutes where a human would have given up.
- **Fun preservation**: The drudgery is removed; what remains is the creative part. Less feeling stuck/blocked.
- **Skill atrophy**: Generation (writing) and discrimination (reading) are different brain capabilities. Manual coding skills will fade; reviewing skills persist.

### Working Style Recommendation

Run a few Claude Code sessions in terminal windows/tabs on the left, IDE on the right for viewing code + manual edits. The AI generates, you discriminate and guide.

### Open Questions

- Does the productivity gap between mean and max engineers grow with AI assistance?
- Do generalists increasingly outperform specialists? (LLMs excel at micro fill-in-the-blanks, humans still needed for macro strategy)
- What does mature LLM coding feel like? StarCraft? Factorio? Conducting an orchestra?
