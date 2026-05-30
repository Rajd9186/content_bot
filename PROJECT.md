# AI Content Intelligence Platform

Multi-agent content generation platform powered by LLMs with a production-grade backend (FastAPI + PostgreSQL + Redis) and a premium dark-theme frontend (Next.js 14 + Tailwind).

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Backend Structure](#backend-structure)
5. [Frontend Structure](#frontend-structure)
6. [API Reference](#api-reference)
7. [Pipeline / Multi-Agent System](#pipeline--multi-agent-system)
8. [Workflow State Machine](#workflow-state-machine)
9. [Provider Routing & Model Assignments](#provider-routing--model-assignments)
10. [Phase 7 Infrastructure](#phase-7-infrastructure)
11. [Running Locally](#running-locally)
12. [Testing](#testing)
13. [Deployment](#deployment)
14. [Environment Variables](#environment-variables)

---

## Overview

The AI Content Intelligence Platform is a multi-agent content generation system. Users submit a topic, audience, tone, and goals; a pipeline of specialized LLM agents (research, planner, writer, SEO, fact-checker, compliance, finalizer) collaboratively produces polished content.

**Key capabilities:**
- 7-agent content generation pipeline with human review gate
- Orchestration engine with full state machine (11 stages)
- Provider failover chain: OpenAI → Groq → Ollama (gpt-oss:120b)
- SSE-based live streaming of pipeline execution events
- Redis-backed job queues, distributed locks, and pub/sub
- PostgreSQL persistence with Alembic migrations
- Graceful degradation — all features work without Redis or PostgreSQL
- Circuit breaker per provider (5 failures → OPEN, 60s → HALF_OPEN)
- TPM budget tracking for Groq (12k limit)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Frontend | Next.js 14 App Router, React 18, TypeScript 5.6 |
| UI | Tailwind CSS 3, shadcn/ui, Radix UI primitives, Zustand |
| Database | PostgreSQL 16 + asyncpg |
| Cache / Queue | Redis 7 |
| Vector Store | Qdrant |
| LLM Providers | OpenAI, Anthropic, Groq, Ollama (local) |
| Container | Docker Compose, Dockerfiles |
| Observability | OpenTelemetry, Prometheus, Grafana |

---

## Architecture

### System Context

```
┌──────────────┐     HTTP/REST + SSE     ┌──────────────────┐
│   Browser    │ ──────────────────────▶ │  FastAPI Gateway  │
│ (Next.js 14) │ ◀────────────────────── │   (Port 8000)     │
└──────────────┘                         └────────┬─────────┘
                                                  │
                    ┌─────────────────────────────┼──────────────────────┐
                    │                             │                      │
                    ▼                             ▼                      ▼
           ┌───────────────┐           ┌──────────────────┐   ┌──────────────────┐
           │   PostgreSQL   │           │      Redis       │   │  LLM Providers   │
           │  (asyncpg)     │           │  queues/pubsub   │   │ OpenAI/Groq/Ollama│
           └───────────────┘           └──────────────────┘   └──────────────────┘
```

### Bounded Contexts

| Domain | Type | Responsibility |
|---|---|---|
| **Content** | Core | Source management, article lifecycle, metadata |
| **Analysis** | Supporting | AI-driven extraction, classification, summarization |
| **Workflow** | Generic | Job orchestration, state machine, saga coordination |
| **Identity** | Core | Auth, RBAC, workspace management |
| **Agent** | Supporting | LLM provider abstraction, prompt templates, token tracking |

### Module Dependency Rule

```
identity (no deps)
  └── content
       └── workflow
            └── analysis
```

No domain imports directly from another domain's infrastructure layer. Communication uses domain events and ID references.

---

## Backend Structure

```
backend/
├── app/
│   ├── main.py                          # FastAPI app factory, lifespan (wires workers)
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings (APP_ prefix)
│   │   ├── database.py                  # SQLAlchemy async engine + session factory
│   │   ├── deps.py                      # FastAPI DI (get_db, get_orchestrator)
│   │   ├── exceptions.py                # Exception hierarchy
│   │   └── logging.py                   # Structured JSON logging
│   │
│   ├── api/v1/
│   │   ├── router.py                    # Route aggregation
│   │   └── endpoints/
│   │       ├── health.py                # /health, /health/ready
│   │       ├── pipeline_api.py          # Full pipeline CRUD + SSE streaming
│   │       └── orchestration.py         # Workflow orchestration CRUD
│   │
│   ├── infrastructure/
│   │   ├── models/
│   │   │   ├── pipeline.py              # PipelineRun SQLAlchemy model
│   │   │   └── ─── __init__.py
│   │   ├── repositories/
│   │   │   ├── pipeline_repository.py   # PipelineRepository + CheckpointRepository
│   │   │   └── __init__.py
│   │   ├── unit_of_work.py              # UnitOfWork with lazy property imports
│   │   ├── messaging/
│   │   │   └── redis_client.py          # Redis client, queues, pub/sub, locks
│   │   ├── sse/
│   │   │   ├── manager.py               # SSEConnectionManager (Redis pub/sub bridge)
│   │   │   └── __init__.py
│   │   ├── workers/
│   │   │   ├── pipeline_worker.py       # Redis queue consumer for pipeline execution
│   │   │   ├── recovery_worker.py       # Zombie detection + startup recovery
│   │   │   └── __init__.py
│   │   ├── failover/
│   │   │   ├── provider_failover.py     # Circuit breaker + provider failover chains
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── pipeline/
│   │   ├── state.py                     # PipelineState, NodeResult, HumanReview
│   │   ├── graph.py                     # WorkflowPipeline (7-agent DAG)
│   │   ├── router.py                    # ProviderRouter (model selection)
│   │   └── agents/
│   │       └── base.py                  # BasePipelineAgent
│   │
│   ├── orchestration/
│   │   ├── orchestrator.py              # Orchestrator singleton
│   │   ├── stages.py                    # WorkflowStage, WorkflowStatus, WorkflowRun
│   │   └── validators.py                # Validation logic
│   │
│   ├── agents/
│   │   └── provider/
│   │       ├── factory.py               # ProviderFactory
│   │       ├── base.py                  # BaseProvider abstract class
│   │       ├── openai.py                # OpenAIProvider
│   │       ├── anthropic.py             # AnthropicProvider
│   │       ├── groq.py                  # GroqProvider
│   │       ├── ollama.py                # OllamaProvider
│   │       └── local.py                 # LocalProvider
│   │
│   └── middleware/
│       ├── correlation.py               # X-Correlation-ID propagation
│       ├── logging.py                   # Request/response logging
│       └── errors.py                    # Global error handler
│
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 0001_initial.py
│       ├── 0002_add_checkpoints.py
│       └── 0003_add_pipeline_runs.py
│
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_pipeline_api.py
│   ├── infrastructure/                  # Phase 7-specific tests
│   │   ├── test_sse_manager.py
│   │   ├── test_provider_failover.py
│   │   ├── test_pipeline_worker.py
│   │   ├── test_recovery_worker.py
│   │   └── test_pipeline_api_fallback.py
│   ├── agents/
│   ├── integration/
│   │   └── test_orchestration_api.py
│   └── ...
│
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── .env
```

---

## Frontend Structure

```
frontend/src/
├── app/
│   ├── layout.tsx                       # Root layout (fonts, metadata, providers)
│   ├── page.tsx                         # Landing page
│   ├── globals.css                      # Tailwind + shadcn theme (dark-first)
│   ├── (auth)/
│   │   └── login/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx                   # Dashboard layout with sidebar nav
│       └── page.tsx                     # 8-section dashboard (dynamic imports)
│
├── components/
│   ├── ui/                              # shadcn/ui primitives
│   │   ├── button.tsx
│   │   ├── badge.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── separator.tsx
│   │   ├── sheet.tsx
│   │   ├── tabs.tsx
│   │   ├── toast.tsx
│   │   └── tooltip.tsx
│   ├── dashboard/
│   │   ├── ContentPipelineSection.tsx
│   │   ├── PipelineListSection.tsx
│   │   ├── AnalyticsSection.tsx
│   │   ├── WorkspaceSection.tsx
│   │   ├── SettingsSection.tsx
│   │   ├── AgentMonitorSection.tsx
│   │   ├── OrchestrationSection.tsx
│   │   └── side-nav.tsx
│   └── ThemeToggle.tsx
│
├── hooks/
│   ├── use-auth.ts
│   └── use-pipeline.ts
│
├── lib/
│   ├── api-client.ts                    # Typed API client (axios)
│   ├── websocket.ts                     # WebSocket + SSE helpers
│   └── utils.ts                         # cn(), formatDate(), formatDuration()
│
├── providers/
│   └── auth-provider.tsx
│
├── stores/
│   ├── auth-store.ts                    # Zustand auth state
│   ├── pipeline-store.ts                # Pipeline state (create, run, review)
│   └── ui-store.ts                      # UI state (section, sidebar, theme)
│
└── types/
    └── api.ts                           # Manual API type definitions
```

---

## API Reference

### Health

| Method | Path | Description | Status |
|---|---|---|---|
| GET | `/api/v1/health` | Liveness probe | 200: `{"status":"ok","version":"1.0.0","uptimeSeconds":N}` |
| GET | `/api/v1/health/ready` | Readiness probe (includes Redis check) | 200 if DB + Redis reachable |

### Pipeline (Content Generation)

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/content-pipeline/pipeline/start?topic=...&audience=...&tone=...&goals=...` | Create a new pipeline run |
| POST | `/api/v1/content-pipeline/pipeline/{id}/run?skip_review=false` | Execute pipeline (inline or enqueue to Redis worker) |
| GET | `/api/v1/content-pipeline/pipeline/{id}` | Get pipeline status + node results |
| GET | `/api/v1/content-pipeline/pipeline/{id}/content?include_draft=false` | Get final/draft content |
| GET | `/api/v1/content-pipeline/pipeline/{id}/timeline` | Get node execution timeline |
| GET | `/api/v1/content-pipeline/pipeline/{id}/events` | SSE stream of pipeline events |
| POST | `/api/v1/content-pipeline/pipeline/{id}/review?action=approved&comments=...&reviewer_id=...` | Submit human review |
| POST | `/api/v1/content-pipeline/pipeline/{id}/cancel` | Cancel pipeline |

### Orchestration

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/orchestration/workflows?workspace_id=...&correlation_id=...` | Create orchestration workflow |
| POST | `/api/v1/orchestration/workflows/{id}/run?use_pipeline=false` | Execute workflow (stub or real pipeline adapter) |
| POST | `/api/v1/orchestration/workflows/{id}/resume?current_stage=...` | Resume workflow from a stage |
| POST | `/api/v1/orchestration/workflows/{id}/cancel?reason=manual` | Cancel workflow |
| GET | `/api/v1/orchestration/workflows/{id}` | Get workflow status |
| GET | `/api/v1/orchestration/workflows/{id}/stages` | Get completed stage results |

### Workflows (Jobs)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/workflows/jobs` | List jobs |
| POST | `/api/v1/workflows/jobs/{id}/submit` | Submit a job |
| POST | `/api/v1/workflows/jobs/{id}/cancel` | Cancel a job |
| GET | `/api/v1/workflows/jobs/{id}` | Get job status |

### Content

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/content/items` | List content items |

---

## Pipeline / Multi-Agent System

### 7-Agent Pipeline

The pipeline executes content generation through 7 specialized agents in sequence:

```
topic → research → planner → writer → seo → fact_checker → compliance → finalizer → content
                                          │
                                          ▼
                                     human_review (gate)
                                       │        │
                                  approved   changes_requested
                                       │        │
                                  finalizer    writer (re-edit)
```

### Agent Responsibilities

| Agent | Role | Default Provider |
|---|---|---|
| **research** | Gathers and synthesizes source material on the topic | Ollama (gpt-oss:120b) |
| **planner** | Creates a structured outline with sections and key points | Ollama (gpt-oss:120b) |
| **writer** | Generates the full article draft | Groq |
| **seo** | Optimizes for search keywords and metadata | Ollama (gpt-oss:120b) |
| **fact_checker** | Verifies factual accuracy of claims | Ollama (gpt-oss:120b) |
| **compliance** | Checks content against guidelines and policies | Ollama (gpt-oss:120b) |
| **finalizer** | Applies final polish, formatting, and review feedback | Groq |

### PipelineState

Each pipeline run has a `PipelineState` object tracking:

- `workflow_id`, `workspace_id`, `correlation_id`
- `topic`, `audience`, `tone`, `goals`
- `current_node` — which agent is currently executing
- `node_results` — dict of node name → `NodeResult` (status, output, tokens, latency)
- `draft_content`, `final_content` — generated text
- `research_data`, `seo_metadata`, `fact_check_results`, `compliance_results`
- `human_review` — review action (approved/rejected/changes_requested)
- `errors` — list of error strings
- `created_at`, `updated_at`

---

## Workflow State Machine

### Stages

```
INIT → PLANNING → RESEARCH → SYNTHESIS → OUTLINING → WRITING →
  VALIDATION → SEO → FACT_CHECK → FINALIZATION → PUBLISHED
                                              ↘ FAILED
```

### Transitions

| From | To | Trigger | Side Effect |
|---|---|---|---|
| INIT | PLANNING | submit | Emit job started event |
| PLANNING | RESEARCH | plan_ready | — |
| RESEARCH | SYNTHESIS | research_complete | — |
| SYNTHESIS | OUTLINING | synthesis_complete | — |
| OUTLINING | WRITING | outline_ready | — |
| WRITING | VALIDATION | draft_complete | — |
| VALIDATION | SEO | validation_passed | — |
| VALIDATION | WRITING | rewrite_requested | Flag rewrite iteration |
| SEO | FACT_CHECK | seo_optimized | — |
| FACT_CHECK | FINALIZATION | fact_check_passed | — |
| FACT_CHECK | WRITING | rewrite_requested | Flag rewrite |
| FINALIZATION | PUBLISHED | finalize | Emit job completed |
| Any | FAILED | *_error | Record error details |
| FAILED | INIT | retry | Increment retry count |

### Concurrency

- Optimistic locking via `version` column (`UPDATE ... WHERE version = :current`)
- Redis distributed lock per job: `job:{id}:lock` (TTL = 30s)
- All transitions logged to immutable `ExecutionLog` table

---

## Provider Routing & Model Assignments

### Provider Failover Chains

| Agent Type | Primary | Secondary | Fallback |
|---|---|---|---|
| writer | Groq | OpenAI | Ollama |
| finalizer | Groq | OpenAI | Ollama |
| research | OpenAI | Groq | Ollama |
| planner | OpenAI | Groq | Ollama |
| seo | OpenAI | Groq | Ollama |
| fact_checker | OpenAI | Groq | Ollama |
| compliance | OpenAI | Groq | Ollama |

### Groq Models

| Complexity | Models |
|---|---|
| Small | `llama-3.1-8b-instant` |
| Medium | `groq/compound` |
| Premium | `llama-3.3-70b-versatile` |

Premium is used for finalizer and large writer tasks (>4000 tokens). Default model: `llama-3.3-70b-versatile`.

### Ollama

Provider name: `gpt-oss` (with gpt-oss host prefix)
Model: `gpt-oss:120b` (always, all agents except writer/finalizer)

### Circuit Breaker

| Parameter | Value |
|---|---|
| Failure threshold | 5 consecutive failures |
| Reset timeout | 60 seconds |
| States | CLOSED → OPEN (after 5 failures) → HALF_OPEN (after 60s) |
| Per-provider | Separate circuit per provider (openai, groq, ollama) |

### Token Budget

- Groq: 12,000 TPM (tokens per minute) limit
- Max 2 concurrent Groq executions
- Rate limit detection triggers automatic fallback to next smaller model or Ollama

### Concurrency Control

- Semaphore-limited: max 2 concurrent premium executions (Groq writer/finalizer)
- Token budget tracker with 60-second sliding window
- Redis-backed TPM counter for cross-node coordination when available

---

## Phase 7 Infrastructure

### Persistence

| Component | Description |
|---|---|
| `PipelineRun` model | SQLAlchemy model with JSONB columns for state, node_results, errors |
| `PipelineRepository` | Full CRUD: `save_pipeline_state()`, `get_by_workflow_id()`, `get_active_pipelines()`, `get_zombie_pipelines()`, `heartbeat()`, `update_status()` |
| `CheckpointRepository` | `save_checkpoint()`, `get_latest_checkpoint()` for workflow runs |
| `UnitOfWork` | Lazy property imports for `pipelines` and `checkpoints` repos |
| Alembic `0003` | Creates `pipeline_runs` table with indexes on `workflow_id`, `status`, `heartbeat_at` |

### Graceful Degradation

When PostgreSQL is unavailable:
- `_save_state()` writes to `_memory_fallback` dict (keyed by workflow_id)
- `_load_state()` checks DB first, then memory fallback
- Orchestration endpoints use `_workflow_run_cache` dict
- All tests pass without DB (362 original + 55 new)

### SSE Streaming

| Component | Description |
|---|---|
| `SSEConnectionManager` | Manages per-workflow `asyncio.Queue` sets, Redis pub/sub bridge |
| Max connections | 200 total |
| Queue limit | 256 items per queue (overflow eviction) |
| Heartbeat | Every 15 seconds |
| Events | `connected`, `node_completed`, `pipeline_completed`, `pipeline_failed`, `pipeline_cancelled`, `pipeline_recovered` |

### Workers

| Worker | Description |
|---|---|
| `PipelineWorker` | Redis BLPOP consumer (2s timeout), semaphore-limited (5 concurrent), checkpoint-per-node + SSE broadcast, 30s heartbeat for zombie detection |
| `PipelineRecoveryWorker` | `RecoveryService` on startup (recovers pending/running), zombie detection every 60s (stale heartbeat > 5 min → mark failed) |

---

## Running Locally

### Option 1: Full Stack (Docker)

```bash
docker compose -f docker/dev/docker-compose.yml up -d
```

Services:
| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/v1/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Qdrant | localhost:6333 |

### Option 2: Local Development (Infra in Docker, Code Native)

```bash
# 1. Start dependencies
docker compose -f docker/dev/docker-compose.yml up -d postgres redis qdrant

# 2. Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Option 3: Fully Manual (No Docker)

- Run PostgreSQL and Redis locally, create database `ai_content_intel`
- Set `APP_DATABASE_URL` and `APP_REDIS_URL` in `backend/.env`
- Follow Option 2 steps 2-3

### Set API Keys

Edit `backend/.env`:
```bash
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
```

Without API keys, the app runs but LLM calls will fail. The pipeline still works in stub mode and all persistence, SSE, worker, and recovery features work.

---

## Testing

```bash
# Run all tests (417 total)
cd backend && pytest

# Run specific test file
cd backend && pytest tests/test_pipeline_api.py -v

# Run Phase 7 infrastructure tests
cd backend && pytest tests/infrastructure/ -v

# Run orchestration integration tests
cd backend && pytest tests/integration/test_orchestration_api.py -v

# Frontend tests
cd frontend && npm test
```

### Test Breakdown

| Suite | Count |
|---|---|
| Original backend tests | 362 |
| Phase 7 infrastructure tests | 55 |
| **Total** | **417** |

All pass. Zero regressions.

---

## Deployment

### Docker Compose (Local/Dev)

```bash
make build
make up
```

### Kubernetes (Production)

```bash
kubectl apply -f k8s-deployment.yaml
```

### Cloud (AWS ECS, GCP Cloud Run, Azure Container Apps)

- Build Docker images and push to container registry
- Set environment variables in cloud console
- Expose port 8000

See `DEPLOYMENT.md` for detailed instructions.

### Scaling

| Component | Recommendation |
|---|---|
| Backend replicas | 2-10 (auto-scaled) |
| Backend resources | 512Mi-1Gi RAM, 500m-1000m CPU |
| PostgreSQL | Read replicas for heavy load |
| Redis | Cluster mode for HA |

---

## Environment Variables

All `APP_*` variables set via `backend/.env`. Prefix: `APP_`.

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | AI Content Intelligence Platform | — |
| `VERSION` | 1.0.0 | — |
| `API_V1_STR` | /api/v1 | API version prefix |
| `ENVIRONMENT` | development | — |
| `DEBUG` | true | — |
| `BACKEND_CORS_ORIGINS` | ["http://localhost:3000","http://localhost:8000"] | CORS whitelist |
| `DATABASE_URL` | postgresql+asyncpg://postgres:postgres@localhost:5432/ai_content_intel | Async PostgreSQL DSN |
| `DATABASE_POOL_SIZE` | 20 | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | 10 | Max overflow connections |
| `REDIS_URL` | redis://localhost:6379 | Redis DSN |
| `LOG_LEVEL` | INFO | Logging level |
| `JWT_SECRET` | change-me-in-production | JWT signing key |
| `JWT_ALGORITHM` | HS256 | JWT algorithm |
| `JWT_EXPIRATION_MINUTES` | 15 | Token expiry |
| `RATE_LIMIT_TTL` | 60 | Rate limit window (s) |
| `RATE_LIMIT_MAX` | 100 | Max requests per window |
| `OTLP_ENDPOINT` | None | OpenTelemetry endpoint |
| `METRICS_PORT` | 9464 | Prometheus metrics port |

Non-prefixed vars in `.env`:
| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GROQ_API_KEY` | Groq API key |
| `LOCAL_MODEL_URL` | Local model endpoint (default: http://localhost:8000/v1) |

Frontend vars (in `frontend/.env`):
| Variable | Default |
|---|---|
| `NEXT_PUBLIC_API_URL` | http://localhost:8000/api/v1 |
| `NEXT_PUBLIC_WS_URL` | ws://localhost:8000/api/v1 |
| `NEXT_PUBLIC_APP_NAME` | AI Content Intelligence Platform |

---

## Quality Commands

```bash
make lint          # Ruff (backend) + ESLint (frontend)
make format        # Ruff format (backend) + Prettier (frontend)
make test          # Pytest (backend) + Jest (frontend)
make typecheck     # Pyright (backend) + tsc (frontend)
make db-migrate    # Alembic upgrade head
```

---

## Project Status

- **Tests:** 417 passing, 0 failing
- **API endpoints:** 21 all verified working
- **Phases completed:** 1-7 (Foundation → Enterprise Frontend → Infrastructure)
- **LLM providers:** OpenAI, Anthropic, Groq, Ollama, local
- **Persistence:** PostgreSQL (with in-memory fallback)
- **Queue:** Redis (with degraded inline execution)
- **Streaming:** SSE via Redis pub/sub
- **Resilience:** Circuit breakers, provider failover, zombie recovery, dead-letter handling
