# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI service (apps in `backend/apps/api`, shared logic in `backend/packages`, migrations in `backend/migrations`).
- `frontend/`: Next.js 14 app (source in `frontend/src`).
- `tests/`: Pytest suite for backend and integration coverage.
- `doc/`: Architecture and product documentation.
- `scripts/`: Local setup helpers.

## Build, Test, and Development Commands
- `make install`: Install backend (pip) and frontend (npm) dependencies.
- `make dev`: Run backend (`uvicorn`) and frontend (`next dev`) locally.
- `make up` / `make down`: Start/stop Docker Compose services.
- `make test`: Run backend pytest + frontend tests.
- `make test-backend` / `make test-frontend`: Run tests for one side.
- `make format` / `make lint`: Run Black/Prettier and Ruff/ESLint.
- Frontend build: `cd frontend && npm run build`.

## Coding Style & Naming Conventions
- Python: Black + Ruff, 100-char line length (`backend/pyproject.toml`).
- TypeScript: Prettier + ESLint; Tailwind for styling.
- Tests: `tests/test_*.py`, classes `Test*`, functions `test_*` (see `tests/pytest.ini`).

## Testing Guidelines
- Framework: Pytest with markers `unit`, `integration`, `slow`, `database`, `api`.
- Run all: `pytest tests/` or `make test-backend`.
- Coverage: `pytest --cov=backend/packages --cov-report=html` (outputs to `htmlcov/`).
- Keep new tests close to affected modules and follow existing fixtures in `tests/conftest.py`.

## Commit & Pull Request Guidelines
- Commit format (Conventional Commits): `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`.
- Typical flow: branch from main, run `make test` and `make format`, then open a PR.
- PRs should describe changes, link issues if applicable, and note test coverage updates.

## Data Contracts & Configuration
- Keep schemas in sync between `backend/packages/shared/schemas.py` and
  `frontend/src/types/brief.ts`.
- Local config uses `.env` in `backend/`; Docker Compose is the default dev path.
