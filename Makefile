# AI Content Intelligence Platform — Development Task Runner
.PHONY: help build up down restart logs ps \
        shell-backend shell-frontend shell-db \
        lint format test \
        db-migrate db-reset db-shell \
        clean setup

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ──────────────────────────────────────────────────────────────────

build: ## Build all Docker images
	docker compose -f docker/dev/docker-compose.yml build

up: ## Start all services in detached mode
	docker compose -f docker/dev/docker-compose.yml up -d

down: ## Stop all services
	docker compose -f docker/dev/docker-compose.yml down

restart: down up ## Restart all services

logs: ## Follow logs for all services
	docker compose -f docker/dev/docker-compose.yml logs -f

ps: ## List running services
	docker compose -f docker/dev/docker-compose.yml ps

# ── Development Shells ──────────────────────────────────────────────────────

shell-backend: ## Open a shell in the backend container
	docker compose -f docker/dev/docker-compose.yml exec backend /bin/bash

shell-frontend: ## Open a shell in the frontend container
	docker compose -f docker/dev/docker-compose.yml exec frontend /bin/sh

shell-db: ## Open a SQL shell in the database
	docker compose -f docker/dev/docker-compose.yml exec postgres psql -U postgres ai_content_intel

# ── Backend Commands ────────────────────────────────────────────────────────

backend-dev: ## Run backend locally with hot reload
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-lint: ## Lint backend with ruff
	cd backend && ruff check .

backend-format: ## Format backend with ruff
	cd backend && ruff format .

backend-test: ## Run backend tests
	cd backend && pytest -v

backend-typecheck: ## Type check backend with pyright
	cd backend && pyright .

# ── Frontend Commands ───────────────────────────────────────────────────────

frontend-dev: ## Run frontend locally with hot reload
	cd frontend && npm run dev

frontend-lint: ## Lint frontend
	cd frontend && npm run lint

frontend-format: ## Format frontend
	cd frontend && npm run format

frontend-test: ## Run frontend tests
	cd frontend && npm test

frontend-typecheck: ## Type check frontend
	cd frontend && npm run typecheck

generate-types: backend-types frontend-types ## Generate all types

backend-types: ## Generate openapi.json from backend
	cd backend && python -c "from app.main import app; import json; json.dump(app.openapi(), open('openapi.json','w'))"

frontend-types: ## Generate TypeScript types from OpenAPI spec
	cd frontend && npm run generate-types 2>/dev/null || echo "Warning: generate-types requires the backend to be running on localhost:8000"

# ── Combined Quality ────────────────────────────────────────────────────────

lint: backend-lint frontend-lint ## Lint all code

format: backend-format frontend-format ## Format all code

test: backend-test frontend-test ## Run all tests

typecheck: backend-typecheck frontend-typecheck ## Type check all code

# ── Database ─────────────────────────────────────────────────────────────────

db-migrate: ## Run database migrations
	cd backend && alembic upgrade head

db-migrate-create: ## Create a new migration
	cd backend && alembic revision --autogenerate -m "$(message)"

db-reset: ## Reset database (drop all tables)
	cd backend && alembic downgrade base && alembic upgrade head

db-shell: ## Open database shell
	docker compose -f docker/dev/docker-compose.yml exec postgres psql -U postgres ai_content_intel

# ── Maintenance ─────────────────────────────────────────────────────────────

clean: ## Clean build artifacts
	rm -rf backend/.ruff_cache
	rm -rf frontend/.next
	rm -rf **/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

setup: ## Install all dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# ── Local Dev (no Docker) ───────────────────────────────────────────────────

dev-db: ## Start infrastructure only (Postgres, Redis, Qdrant)
	docker compose -f docker/dev/docker-compose.yml up -d postgres redis qdrant

dev: ## Run full stack locally (requires dev-db running)
	@echo "Starting backend on http://localhost:8000"
	@echo "Starting frontend on http://localhost:3000"
	@$(MAKE) backend-dev & $(MAKE) frontend-dev & wait
