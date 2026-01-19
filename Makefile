.PHONY: help install dev up down logs test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed"

dev: ## Start development servers locally
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend development server
	cd backend && uvicorn apps.api.main:app --reload --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

up: ## Start all services with Docker Compose
	docker-compose up -d
	@echo "✅ Services started"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down: ## Stop all Docker Compose services
	docker-compose down

logs: ## Show Docker Compose logs
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test

test-backend: ## Run backend tests only
	cd backend && pytest

test-frontend: ## Run frontend tests only
	cd frontend && npm test

clean: ## Clean up build artifacts and caches
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned"

format: ## Format code (black + prettier)
	cd backend && black .
	cd frontend && npm run format || true

lint: ## Lint code
	cd backend && ruff check .
	cd frontend && npm run lint

reset-db: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d postgres redis
	@echo "⚠️  Database reset complete"

db-migrate: ## Create a new database migration
	@read -p "Migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

db-upgrade: ## Apply database migrations
	cd backend && alembic upgrade head

db-downgrade: ## Rollback last migration
	cd backend && alembic downgrade -1

db-init: ## Initialize database (create tables + seed data)
	cd backend && python scripts/init_db.py

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U morning_brief -d morning_brief
