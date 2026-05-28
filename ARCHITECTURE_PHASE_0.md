# AI Content Intelligence Platform — Phase 0 Architectural Constitution

> **Status:** Ratified · **Version:** 1.0.0 · **Scope:** Foundation architecture, no implementation  
> **Governance:** All Phase 1+ work must conform to this constitution. Deviations require architecture board approval.

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Repository Structure](#2-repository-structure)
3. [Backend Folder Structure (DDD / Hexagonal)](#3-backend-folder-structure-ddd--hexagonal)
4. [Frontend Folder Structure (Feature-Sliced Design)](#4-frontend-folder-structure-feature-sliced-design)
5. [Domain-Driven Architecture Boundaries](#5-domain-driven-architecture-boundaries)
6. [Service Responsibilities](#6-service-responsibilities)
7. [Event Naming Conventions](#7-event-naming-conventions)
8. [API Naming Conventions](#8-api-naming-conventions)
9. [Workflow Stage Definitions](#9-workflow-stage-definitions)
10. [State Machine Specification](#10-state-machine-specification)
11. [Correlation ID Strategy](#11-correlation-id-strategy)
12. [Logging Standards](#12-logging-standards)
13. [OpenAPI Standards](#13-openapi-standards)
14. [DTO / Schema Standards](#14-dto--schema-standards)
15. [Frontend Type Generation Strategy](#15-frontend-type-generation-strategy)
16. [Database Naming Conventions](#16-database-naming-conventions)
17. [Environment Configuration Strategy](#17-environment-configuration-strategy)
18. [Multi-Agent Contract Standards](#18-multi-agent-contract-standards)
19. [Retry Architecture Standards](#19-retry-architecture-standards)
20. [Validation Architecture Standards](#20-validation-architecture-standards)
21. [Observability Architecture Standards](#21-observability-architecture-standards)
22. [System Context Diagram](#22-system-context-diagram)

---

## 1. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Project Structure | Separate directories (npm workspaces planned) | Backend and frontend are independent projects; npm workspaces for future monorepo transition |
| Backend | FastAPI (Python 3.11) | Async-native, Pydantic v2, auto OpenAPI, high throughput |
| Frontend | Next.js 14 App Router + React 18 | Server components, streaming SSR, edge runtime |
| Workers | Celery / Arq (Python background tasks) | Native Python async task queue, Redis broker |
| Shared language | TypeScript 5.4+ (strict) — frontend; Python 3.11 — backend | Type-safe on each side of the boundary |
| API contract | Pydantic v2 (backend) + Zod 3.x (frontend) + OpenAPI 3.1 bridge | Runtime validation on both sides, synchronized via openapi-typescript |
| Database ORM | SQLAlchemy 2.0 (async) + Alembic | Mature async ORM, explicit migration control |
| Cache / Pub-Sub | Redis 7.x | Session store, rate limiter, job queue, event bus |
| Vector store | Qdrant (self-hosted or cloud) | Purpose-built vector DB, gRPC-native, filtering |
| Message broker | Redis Streams (lightweight) / RabbitMQ (future) | At-least-once delivery, consumer groups |
| Observability | OpenTelemetry + Prometheus + Grafana | Vendor-neutral telemetry, RED metrics |
| Container | Docker Compose (dev) + Kubernetes (prod) | Dev/prod parity with progressive complexity |

---

## 2. Repository Structure

```
/
├── .github/
│   └── workflows/
│       ├── ci.yml                       # Lint, test, build for backend + frontend
│
├── backend/                             # FastAPI API Gateway (port 8000)
│   ├── app/
│   │   ├── core/                        # Config, logging, database, exceptions
│   │   ├── api/v1/                      # Versioned REST endpoints
│   │   ├── middleware/                   # Correlation ID, request logging, errors
│   │   └── schemas/                     # Pydantic v2 models
│   ├── tests/
│   ├── alembic/                         # Database migrations
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/                            # Next.js Frontend (port 3000)
│   ├── src/
│   │   ├── app/                         # Next.js App Router
│   │   ├── components/                  # shadcn/ui components
│   │   ├── lib/                         # API client, WebSocket, utilities
│   │   ├── hooks/                       # React hooks
│   │   ├── providers/                   # Auth context provider
│   │   ├── stores/                      # Zustand state management
│   │   └── types/                       # TypeScript type definitions
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
│
├── docker/
│   ├── dev/
│   │   └── docker-compose.yml           # Full development stack
│   └── prod/
│       └── docker-compose.yml           # Production configuration
│
├── Makefile                             # Development task runner
├── .pre-commit-config.yaml
├── .env.example
├── .gitignore
└── README.md
```

No monorepo orchestrator. Backend and frontend are independent projects under `/backend` and `/frontend`, each with their own `package.json` / `pyproject.toml`. A root `Makefile` coordinates cross-project tasks.

---

## 3. Backend Folder Structure (Phase 1 Foundation)

```
backend/
├── app/
│   ├── core/                            # Cross-cutting concerns
│   │   ├── config.py                    # Pydantic Settings (env prefix APP_)
│   │   ├── logging.py                   # Structured JSON logging
│   │   ├── database.py                  # SQLAlchemy async engine + session factory
│   │   ├── deps.py                      # FastAPI dependency injection functions
│   │   └── exceptions.py                # Application exception hierarchy
│   │
│   ├── middleware/                      # Starlette middleware
│   │   ├── correlation.py               # X-Correlation-ID propagation
│   │   ├── logging.py                   # Request/response timing + logging
│   │   └── errors.py                    # Global error handler
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py                # Root v1 router aggregation
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── health.py            # Liveness + readiness probes
│   │
│   └── schemas/                         # Pydantic v2 models
│       ├── common.py                    # ApiResponse, PaginatedResponse, ErrorResponse
│       └── health.py                    # HealthResponse, ReadinessResponse
│
├── alembic/                             # Database migration directory
│   ├── env.py                           # Async Alembic environment
│   └── versions/                        # Migration files (Phase 2+)
│
├── tests/
│   ├── conftest.py                      # Async test fixtures
│   └── test_health.py                   # Health endpoint tests
│
├── Dockerfile                           # Multi-stage build
├── requirements.txt
├── pyproject.toml
└── .env.example
```

### Module Dependency Rule

```
identity (no deps on other domains)
  └── content (depends on identity for ownership)
       └── workflow (depends on content)
            └── analysis (depends on workflow + content)
```

No domain module may import directly from another domain's **infrastructure** layer. Communication between domains must use:
- Domain events (event bus)
- Application service interfaces (dependency inversion)
- ID references only (not full entity references)

---

## 4. Frontend Folder Structure (Phase 1 Foundation)

```
frontend/src/
├── app/                                 # Next.js App Router
│   ├── (auth)/                          # Auth route group
│   │   └── login/
│   │       └── page.tsx                 # Login page shell
│   ├── (dashboard)/                     # Authenticated route group
│   │   ├── workspace/                   # (Phase 2+)
│   │   ├── content/                     # (Phase 2+)
│   │   ├── analytics/                   # (Phase 2+)
│   │   └── settings/                    # (Phase 2+)
│   │   └── layout.tsx                   # Dashboard layout with sidebar nav
│   ├── layout.tsx                       # Root layout (fonts, metadata, providers)
│   ├── page.tsx                         # Landing page
│   └── globals.css                      # Tailwind CSS variables + shadcn theme
│
├── components/
│   └── ui/                              # shadcn/ui primitives
│       ├── button.tsx                   # CVA button with variants
│       └── badge.tsx                    # Status badge component
│
├── lib/                                 # Infrastructure layer
│   ├── api-client.ts                    # Axios instance, interceptors, typed helpers
│   ├── websocket.ts                     # WebSocket client with reconnection
│   └── utils.ts                         # cn(), formatDate(), formatDuration()
│
├── hooks/                               # Shared React hooks
│   └── use-auth.ts                      # Re-export from auth provider
│
├── providers/                           # React context providers
│   └── auth-provider.tsx                # Auth context with useAuthStore integration
│
├── stores/                              # Zustand state management
│   └── auth-store.ts                    # Auth state with persist middleware
│
└── types/                               # TypeScript type definitions
    └── api.ts                           # API response types, domain types
```

### FSD Import Rules (enforced via ESLint)

```
shared/ ──────────────► all layers
entities/ ────────────► features/, widgets/, pages/
features/ ────────────► widgets/, pages/
widgets/ ─────────────► pages/
pages/ ───────────────► app/ (route segments)
processes/ ───────────► pages/ (higher-order compositions)
```

Layers may only import from layers above (shared is the bottom layer). This prevents circular import chains. A feature may import from entities and shared, but not from widgets or other features. Violations are caught by `@conarti/feature-sliced/eslint-plugin`.

---

## 5. Domain-Driven Architecture Boundaries

### Bounded Contexts

| Domain | Type | Responsibility | Key Entities |
|---|---|---|---|
| **Content** | Core Domain | Source management, article lifecycle, metadata extraction, versioning | `Article`, `Source`, `Metadata`, `ContentHash`, `Tag` |
| **Analysis** | Supporting Domain | AI-driven extraction, classification, sentiment, summarization | `Insight`, `SentimentReport`, `Classification`, `ModelOutput` |
| **Workflow** | Generic Subdomain | Job orchestration, state machine, saga coordination, retry policy | `Job`, `Step`, `ExecutionLog`, `RetryPolicy` |
| **Identity** | Core Domain | Authentication, authorization, RBAC, workspace management | `User`, `Workspace`, `ApiKey`, `Role`, `Permission` |
| **Agent** | Supporting Domain | LLM provider abstraction, prompt templates, token tracking | `Agent`, `PromptTemplate`, `ModelCall`, `TokenUsage` |

### Ubiquitous Language (Glossary)

| Term | Definition |
|---|---|
| Content Item | A piece of source material (article, document, snippet) ingested for analysis |
| Job | A workflow execution instance with a defined state machine |
| Step | An atomic unit of work within a job |
| Insight | A structured finding produced by an analysis agent |
| Agent | A configured LLM instance with a specific model, prompt, and output schema |
| Workspace | An organizational boundary isolating users, content, and jobs |
| Execution Log | An immutable record of every state transition within a job |

### Bounded Context Map

```mermaid
graph TD
    Identity[Identity Context] --> Content[Content Context]
    Content --> Workflow[Workflow Context]
    Workflow --> Analysis[Analysis Context]
    Analysis --> Agent[Agent Context]
    
    Content -.->|Domain Events| Workflow
    Workflow -.->|Domain Events| Analysis
    Analysis -.->|Domain Events| Content
    
    subgraph "Anti-Corruption Layer"
        Agent -- "LLM Provider Adapter" --> OpenAI
        Agent -- "LLM Provider Adapter" --> Anthropic
        Agent -- "LLM Provider Adapter" --> Local
    end
```

---

## 6. Service Responsibilities

### API Gateway (`backend/`)

| Responsibility | Details |
|---|---|
| Request routing | Map incoming HTTP requests to FastAPI routers |
| Authentication | Validate JWT tokens, API keys, session cookies |
| Authorization | Enforce RBAC policies per route |
| Rate limiting | Per-user / per-workspace / per-IP throttling (Redis-backed) |
| Input validation | Pydantic model validation at router boundary (fail-fast) |
| Response shaping | Standard envelope (`success`, `data`, `error`, `meta`) |
| API versioning | URL-prefix versioning (`/v1/`, `/v2/`) |
| CORS | Strict white-list per environment |
| Swagger/OpenAPI | Auto-generated from Pydantic models + FastAPI metadata |

### Workflow Engine (`backend/` — Workflow domain, Phase 2+)

| Responsibility | Details |
|---|---|
| State machine execution | Thread-safe state transitions with optimistic concurrency |
| Saga coordination | Long-running transaction with compensation handlers |
| Job scheduling | Delayed execution, cron triggers, batch dispatch |
| Retry management | Exponential backoff with jitter, dead-letter after max retries |
| Timeout enforcement | Hard per-step timeout, escalation on breach |
| Execution logging | Immutable append-only log of every transition |

### Agent Service (`backend/` — Agent domain, Phase 2+)

| Responsibility | Details |
|---|---|
| LLM provider abstraction | Unified interface for OpenAI, Anthropic, local models |
| Prompt management | Versioned prompt templates with variable injection |
| Output parsing | Structured output extraction (JSON mode, function calling) |
| Token tracking | Per-call token usage, workspace-level quota enforcement |
| Model routing | Model selection based on task type, cost, latency targets |
| Response validation | Validate structured output against expected schema |

### Vector Service (`backend/` — Analysis domain, Phase 2+)

| Responsibility | Details |
|---|---|
| Embedding generation | Text chunking + embedding via configured provider |
| Vector storage | Upsert + delete operations on Qdrant |
| Similarity search | Hybrid search (vector + keyword + metadata filter) |
| Context retrieval | RAG context assembly for agent prompts |
| Index management | Collection lifecycle, re-index triggers |

---

## 7. Event Naming Conventions

### Schema

All events follow **CloudEvents 1.0** specification with the following naming pattern:

```
<domain>.<entity>.<action>.<version>
```

### Event Catalog

| Event | Version | Producer | Consumer(s) | Trigger |
|---|---|---|---|---|
| `content.article.created.v1` | 1 | Content domain | Workflow, Search indexer | Article persisted |
| `content.article.updated.v1` | 1 | Content domain | Search indexer, Cache evictor | Article metadata changed |
| `content.article.deleted.v1` | 1 | Content domain | Search indexer, Cache evictor | Article soft-deleted |
| `content.source.completed.v1` | 1 | Content domain | Workflow domain | Source ingestion finished |
| `analysis.job.started.v1` | 1 | Workflow domain | Analysis domain, WebSocket bridge | Job transitions to PROCESSING |
| `analysis.job.completed.v1` | 1 | Workflow domain | Content domain, WebSocket bridge | Job reaches COMPLETED |
| `analysis.job.failed.v1` | 1 | Workflow domain | Content domain, WebSocket bridge | Job reaches FAILED |
| `analysis.stage.changed.v1` | 1 | Workflow domain | WebSocket bridge | Any stage transition |
| `analysis.insight.generated.v1` | 1 | Analysis domain | Content domain | Insight persisted |
| `system.agent.failed.v2` | 2 | Agent domain | Workflow domain, Alert manager | LLM call failure after retries exhausted |
| `system.rate.limit.breached.v1` | 1 | API Gateway | Alert manager | Rate limit threshold exceeded |
| `identity.user.registered.v1` | 1 | Identity domain | Email service, Audit log | User registration completed |
| `identity.workspace.provisioned.v1` | 1 | Identity domain | Billing, Analytics | Workspace creation completed |

### CloudEvent Envelope

```json
{
  "specversion": "1.0",
  "id": "a1b2c3d4-...",
  "source": "/domains/content",
  "type": "content.article.created.v1",
  "datacontenttype": "application/json",
  "subject": "article_12345",
  "time": "2026-05-28T15:00:00Z",
  "correlationid": "corr-uuid-here",
  "data": {
    "articleId": "article_12345",
    "workspaceId": "ws_abc",
    "title": "...",
    "occurredAt": "2026-05-28T15:00:00Z"
  }
}
```

### Delivery Guarantees

| Environment | Broker | Delivery | Ordering |
|---|---|---|---|
| Development | In-process EventEmitter | At-most-once | Not guaranteed |
| Production | Redis Streams / RabbitMQ | At-least-once | Partition-key ordering |

---

## 8. API Naming Conventions

### URL Structure

```
METHOD /v{version}/{resource}/{identifier}[/{sub-resource}]
```

| Component | Convention | Example |
|---|---|---|
| Version | Prefix `v` + integer | `/v1/` |
| Resources | Plural noun, kebab-case | `/content-items/`, `/workflow-executions/` |
| Identifiers | UUID v7 (time-sortable) | `/v1/content-items/01J2X...` |
| Sub-resources | Plural noun | `/v1/content-items/:id/versions/` |
| Query params | camelCase | `?sortBy=createdAt&page=1&pageSize=20` |
| Actions (non-CRUD) | Verb after colon | `POST /v1/content-items/:id:archive`, `POST /v1/workflow-executions/:id:retry` |

### HTTP Methods

| Method | Semantics | Idempotent |
|---|---|---|
| `GET` | Read resource(s) | Yes |
| `POST` | Create or action | No (idempotency key required for mutations) |
| `PUT` | Full replacement | Yes |
| `PATCH` | Partial update | No |
| `DELETE` | Soft-delete (set status) | Yes |

### Response Envelope

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-05-28T15:00:00Z",
    "correlationId": "corr-uuid",
    "version": "1"
  }
}
```

Error response:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title must be between 3 and 200 characters",
    "details": [
      { "field": "title", "message": "Must be between 3 and 200 characters", "code": "TOO_SHORT" }
    ],
    "correlationId": "corr-uuid"
  },
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-05-28T15:00:00Z",
    "correlationId": "corr-uuid",
    "version": "1"
  }
}
```

### Error Code Taxonomy

| HTTP | Code | Description |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request body failed schema validation |
| 400 | `INVALID_STATE_TRANSITION` | Workflow state change not permitted |
| 401 | `UNAUTHENTICATED` | Missing or invalid credentials |
| 403 | `FORBIDDEN` | Authenticated but not authorized |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Version conflict (optimistic locking) |
| 422 | `UNPROCESSABLE_ENTITY` | Business rule violation |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unhandled server error |
| 503 | `SERVICE_UNAVAILABLE` | Downstream dependency unavailable |

---

## 9. Workflow Stage Definitions

### Stage Enum (Python)

```python
# backend/app/orchestration/stages.py
from enum import Enum

class WorkflowStage(str, Enum):
    INIT        = "INIT"         # Initial; not yet submitted for processing
    PLANNING    = "PLANNING"     # Defining research plan and objectives
    RESEARCH    = "RESEARCH"     # Gathering and analyzing source material
    SYNTHESIS   = "SYNTHESIS"    # Merging research findings into coherent structure
    OUTLINING   = "OUTLINING"    # Building article outline
    WRITING     = "WRITING"      # Drafting the article content
    VALIDATION  = "VALIDATION"   # Validating content quality and completeness
    SEO         = "SEO"          # Search engine optimization pass
    FACT_CHECK  = "FACT_CHECK"   # Factual accuracy verification
    FINALIZATION= "FINALIZATION" # Final formatting and compliance check
    PUBLISHED   = "PUBLISHED"    # Terminal: success
    FAILED      = "FAILED"       # Terminal: unrecoverable error
```

### Stage Metadata

Each job carries:

| Field | Type | Description |
|---|---|---|
| `id` | UUID v7 | Unique job identifier |
| `stage` | WorkflowStage | Current workflow stage |
| `workspaceId` | UUID | Owning workspace |
| `createdBy` | UUID | Initiating user |
| `correlationId` | UUID | Trace identifier |
| `retryCount` | integer | Current retry attempt (0-based) |
| `maxRetries` | integer | Configured retry limit |
| `timeoutMs` | integer | Hard timeout per job |
| `startedAt` | datetime | When processing began |
| `completedAt` | datetime \| null | When terminal state reached |
| `error` | ErrorInfo \| null | Terminal error details |
| `version` | integer | Optimistic concurrency token |

---

## 10. State Machine Specification

```mermaid
stateDiagram-v2
    [*] --> INIT
    
    INIT --> PLANNING: submit
    
    PLANNING --> RESEARCH: plan_ready
    PLANNING --> FAILED: planning_error
    
    RESEARCH --> SYNTHESIS: research_complete
    RESEARCH --> FAILED: research_error
    
    SYNTHESIS --> OUTLINING: synthesis_complete
    SYNTHESIS --> FAILED: synthesis_error
    
    OUTLINING --> WRITING: outline_ready
    OUTLINING --> FAILED: outlining_error
    
    WRITING --> VALIDATION: draft_complete
    WRITING --> FAILED: writing_error
    
    VALIDATION --> SEO: validation_passed
    VALIDATION --> WRITING: rewrite_requested
    VALIDATION --> FAILED: validation_failed
    
    SEO --> FACT_CHECK: seo_optimized
    SEO --> FAILED: seo_error
    
    FACT_CHECK --> FINALIZATION: fact_check_passed
    FACT_CHECK --> WRITING: rewrite_requested
    FACT_CHECK --> FAILED: fact_check_error
    
    FINALIZATION --> PUBLISHED: finalize
    FINALIZATION --> FAILED: finalization_error
    
    FAILED --> INIT: retry (if retryCount < maxRetries)
    FAILED --> [*]: dead_letter (retries exhausted)
    PUBLISHED --> [*]
```

### Transition Table

| From | To | Trigger | Guard | Side Effect |
|---|---|---|---|---|
| INIT | PLANNING | `submit` | Owner match, quota check | Emit `analysis.job.started.v1` |
| PLANNING | RESEARCH | `plan_ready` | Capacity available | Log queue wait time |
| PLANNING | FAILED | `planning_error` | — | Record error details |
| RESEARCH | SYNTHESIS | `research_complete` | Research results validated | — |
| RESEARCH | FAILED | `research_error` | — | Record error details |
| SYNTHESIS | OUTLINING | `synthesis_complete` | Merge validated | — |
| SYNTHESIS | FAILED | `synthesis_error` | — | Record error details |
| OUTLINING | WRITING | `outline_ready` | Outline approved | — |
| OUTLINING | FAILED | `outlining_error` | — | Record error details |
| WRITING | VALIDATION | `draft_complete` | Draft meets length/content criteria | — |
| WRITING | FAILED | `writing_error` | — | Record error details |
| VALIDATION | SEO | `validation_passed` | All quality checks passed | — |
| VALIDATION | WRITING | `rewrite_requested` | Quality below threshold | Flag rewrite iteration |
| VALIDATION | FAILED | `validation_failed` | Unrecoverable quality issues | Record error details |
| SEO | FACT_CHECK | `seo_optimized` | SEO analysis complete | — |
| SEO | FAILED | `seo_error` | — | Record error details |
| FACT_CHECK | FINALIZATION | `fact_check_passed` | All citations verified | — |
| FACT_CHECK | WRITING | `rewrite_requested` | Factual errors found | Flag rewrite iteration |
| FACT_CHECK | FAILED | `fact_check_error` | Unrecoverable factual errors | Record error details |
| FINALIZATION | PUBLISHED | `finalize` | All post-checks passed | Emit `analysis.job.completed.v1` |
| FINALIZATION | FAILED | `finalization_error` | — | Record error details |
| FAILED | INIT | `retry` | retryCount < maxRetries | Increment retryCount, emit retry event |
| FAILED | [*] | `dead_letter` | retryCount >= maxRetries | Emit dead-letter alert |

### Concurrency Control

- Every state transition uses **optimistic locking** via the `version` column (`UPDATE ... WHERE version = :current`). If the version does not match, a `409 CONFLICT` is returned and the caller must retry.
- The state machine is a **single-writer-per-job** contract. Redis distributed lock keyed by `job:{id}:lock` is acquired before any transition attempt (TTL = 30s, auto-extend via watchdog).
- All transitions are logged to the immutable `ExecutionLog` table before commit.

### Compensating Actions (Saga)

| Step | Compensating Action | Trigger |
|---|---|---|
| RESEARCH | Purge generated research artifacts | Job enters FAILED from active stage |
| SYNTHESIS | Discard merged findings | Job enters FAILED from SYNTHESIS |
| WRITING | Remove generated draft | Job enters FAILED from WRITING |
| SEO | Rollback SEO metadata changes | Job enters FAILED from SEO |
| FACT_CHECK | Reset citation verification state | Job enters FAILED from FACT_CHECK |
| FINALIZATION | Rollback publish preparation | Job enters FAILED from FINALIZATION |

---

## 11. Correlation ID Strategy

### Header

- **Name:** `X-Correlation-ID`
- **Format:** UUID v4 (example: `550e8400-e29b-41d4-a716-446655440000`)
- **Scope:** Scoped to a single request/job lifecycle
- **Generation:** If not provided by the caller, the API Gateway generates one at the earliest middleware layer

### Propagation Rules

| Boundary | Propagation Method |
|---|---|
| Incoming HTTP | Extract from `X-Correlation-ID` header |
| Internal service calls | Forwarded via HTTP header or message attribute |
| Events | Written to CloudEvent `correlationid` attribute |
| Logs | Included as mandatory `correlationId` field |
| Database | Written to `correlation_id` column on auditable tables |
| WebSocket | Included in initial handshake and every message envelope |
| External API calls | Forwarded in outgoing request headers |

### Trace Context Interop

The `X-Correlation-ID` is distinct from W3C Trace Context (`traceparent`/`tracestate`). Both flow in parallel:

- `X-Correlation-ID`: Business-domain request tracing (user-visible)
- `traceparent`: OpenTelemetry distributed tracing (operations-visible)

The API Gateway generates both on entry and propagates both through all downstream hops.

---

## 12. Logging Standards

### Log Library

- **Runtime:** Python stdlib `logging` with structured JSON formatting
- **Backend:** Custom `JSONFormatter` in `app/core/logging.py` — outputs structured JSON
- **Frontend:** Browser `console` during development; production logging via backend ingest endpoint

### Log Format (JSON)

```json
{
  "timestamp": "2026-05-28T15:00:00.123Z",
  "level": "info",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "serviceName": "api-gateway",
  "environment": "production",
  "message": "Article created successfully",
  "userId": "user_abc123",
  "workspaceId": "ws_def456",
  "jobId": "job_789ghi",
  "durationMs": 342,
  "error": null
}
```

### Mandatory Fields

| Field | Type | Included By |
|---|---|---|
| `timestamp` | ISO 8601 | Logger config (auto) |
| `level` | `trace | debug | info | warn | error | fatal` | Logger config (auto) |
| `correlationId` | UUID v4 | Middleware injection |
| `serviceName` | string | Process startup config |
| `environment` | string | Process startup config |
| `message` | string | Developer |

### Recommended Context Fields

| Field | When |
|---|---|
| `userId` | Authenticated request |
| `workspaceId` | Workspace-scoped operation |
| `jobId` | Job-scoped operation |
| `durationMs` | After any measured operation |
| `httpMethod`, `httpUrl`, `httpStatusCode` | HTTP request logging |
| `error` | Error/fatal level only (include stack trace) |

### Log Levels

| Level | Usage |
|---|---|
| `trace` | Deep debugging (DB queries, external call payloads) |
| `debug` | Development diagnostics |
| `info` | Normal operation milestones (job started, article created) |
| `warn` | Degraded but handled (retry attempt, rate limit approaching) |
| `error` | Operation failure (LLM call failed, validation rejected) |
| `fatal` | Process cannot continue (DB connection lost, port conflict) |

### Sampling

- `trace`/`debug`: Sampled at 1% in production, 100% in development
- `info`/`warn`/`error`/`fatal`: 100% in all environments

### Log Shipping

- **Development:** stdout + `rich` (pretty console output)
- **Production:** stdout (JSON) → container runtime → Loki / Datadog / ELK

---

## 13. OpenAPI Standards

### Specification

- **Format:** OpenAPI 3.1 (JSON Schema Draft 2020-12)
- **Generation:** Auto-generated by FastAPI from Pydantic models + route decorators
- **Endpoint:** `GET /api/v1/openapi.json`
- **UI:** Swagger UI at `GET /api/v1/docs` (FastAPI built-in), ReDoc at `/api/v1/redoc`
- **Export:** `openapi.json` generated at build time via custom script or CI step

### Operation ID Convention

Pattern: `{action}{Entity}{Qualifier}` (camelCase)

| Operation ID | Route |
|---|---|
| `createArticle` | `POST /v1/content-items` |
| `getArticleById` | `GET /v1/content-items/{id}` |
| `listArticles` | `GET /v1/content-items` |
| `archiveArticle` | `POST /v1/content-items/{id}:archive` |
| `startJob` | `POST /v1/workflow-executions` |
| `retryJob` | `POST /v1/workflow-executions/{id}:retry` |

### Response Schema (applied globally)

Every response must conform to:

```yaml
components:
  schemas:
    ApiResponse:
      type: object
      required: [success, data, meta]
      properties:
        success:
          type: boolean
        data:
          oneOf:
            - type: object
            - type: array
          nullable: false
        error:
          type: object
          nullable: true
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
        meta:
          type: object
          required: [requestId, timestamp, correlationId, version]
          properties:
            requestId:
              type: string
              format: uuid
            timestamp:
              type: string
              format: date-time
            correlationId:
              type: string
              format: uuid
            version:
              type: string
```

### Tag Conventions

| Tag | Scope |
|---|---|
| `Content` | Article and source endpoints |
| `Analysis` | Insight and classification endpoints |
| `Workflow` | Job and execution endpoints |
| `Identity` | User, workspace, and auth endpoints |
| `Agents` | Agent configuration endpoints |
| `Health` | Readiness, liveness, and metrics endpoints |

---

## 14. DTO / Schema Standards

### Source of Truth

**Backend:** Pydantic v2 models in `backend/app/schemas/`  
**Frontend:** Zod schemas in `frontend/src/lib/schemas/` (generated from OpenAPI in Phase 2+)  
**Bridge:** OpenAPI 3.1 JSON is the contract between backend and frontend

Backend Pydantic models are the **authoritative definition**. Frontend consumes them via:
1. `openapi-typescript` code generation from `/api/v1/openapi.json`
2. Zod schemas for runtime form validation (mirror structure, added in Phase 2+)

### Backend Schema Naming Convention

```python
# Requests
class CreateArticleRequest(BaseModel): ...
class UpdateArticleRequest(BaseModel): ...
class ListArticlesQuery(BaseModel): ...

# Responses
class ArticleResponse(BaseModel): ...
class JobResponse(BaseModel): ...
class PaginatedResponse(BaseModel, Generic[T]): ...

# Shared
class ContentSource(BaseModel): ...
class ApiResponse(BaseModel, Generic[T]): ...
```

### Schema Package Structure (Phase 1)

```
backend/app/schemas/
├── __init__.py
├── common.py           # ApiResponse, PaginatedResponse, ErrorResponse
└── health.py           # HealthResponse, ReadinessResponse
```

### Pydantic Example

```python
# backend/app/schemas/content/article.py  (Phase 2+)
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ArticleResponse(BaseModel):
    id: UUID
    workspace_id: UUID = Field(alias="workspaceId")
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    status: str
    source_url: str | None = Field(default=None, alias="sourceUrl")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    version: int = Field(gt=0)
```

### DTO Boundaries

| Layer | Uses | Validates With |
|---|---|---|
| API Controller | Pydantic models | FastAPI auto-validation |
| Domain | Domain entities (not DTOs) | Guard clauses, invariant checks |
| API Response | Pydantic models | FastAPI serialization (`response_model`) |
| Frontend | Zod schemas (generated from OpenAPI) | Zod (form validation) |
| Events | Custom CloudEvent data schemas | Pydantic or Zod |

### FastAPI Integration

FastAPI automatically validates request bodies, query parameters, and path parameters against their Pydantic type annotations. The framework returns detailed 422 errors for validation failures without additional plumbing. Custom validators are added via Pydantic's `field_validator` and `model_validator` decorators.

---

## 15. Frontend Type Generation Strategy

### Pipeline

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  FastAPI Server   │────►│  /api/v1/openapi.json │────►│  Generated TS types  │
│  (Pydantic models)│     │  (build artifact)      │     │  (openapi-typescript)│
└──────────────────┘     └──────────────────────┘     └──────────┬───────────┘
                                                                  │
                                            ┌─────────────────────┘
                                            ▼
                                 ┌──────────────────────┐
                                 │  frontend/src/types/  │
                                 │  (auto-generated)     │
                                 │  ↑ Runtime validation │
                                 │  ← TypeScript types   │
                                 └──────────────────────┘
```

### Step-by-Step

1. **Backend** exports `openapi.json` at build time via FastAPI auto-generation from Pydantic models + route decorators
2. **`openapi-typescript`** generates TypeScript type definitions from `openapi.json`
3. **Generated types** are placed in `frontend/src/types/generated/`
4. **Generated Zod schemas** are consumed directly by the frontend for:
   - Runtime form validation (react-hook-form + `@hookform/resolvers/zod`)
   - Type inference (`z.infer<typeof Schema>`) for local mutations
5. **Pre-commit hook** validates that generated types and Zod schemas are in sync (compares structural signatures)
6. **CI pipeline** fails if `openapi.json` changes without regenerating types

### Dual-Source Resolution

| Concern | Source | When |
|---|---|---|
| API response shapes | Generated TS types (openapi-typescript) | Reading API data |
| Request body shapes | Generated TS types | Sending API requests |
| Form validation | Generated Zod schemas | Client-side + server-side |
| Complex derived types | Inferred from Zod schemas | Business logic on client |

---

## 16. Database Naming Conventions

### Naming Rules

| Construct | Convention | Example |
|---|---|---|
| Table names | `snake_case`, plural | `content_items`, `workflow_jobs`, `execution_logs` |
| Column names | `snake_case` | `created_at`, `correlation_id`, `article_id` |
| Primary keys | `id` (UUID v7) | `id` → `01901234-...` |
| Foreign keys | `<singular_table>_id` | `article_id`, `workspace_id` |
| Indexes | `idx_<table>_<columns>` | `idx_content_items_workspace_id`, `idx_jobs_status` |
| Unique constraints | `uq_<table>_<columns>` | `uq_users_email`, `uq_workspaces_slug` |
| Foreign key constraints | `fk_<table>_<referenced>` | `fk_content_items_workspace_id` |
| Check constraints | `ck_<table>_<rule>` | `ck_jobs_status_valid`, `ck_articles_title_length` |
| Enums | PascalCase | `JobStatus`, `ProcessingStage`, `ArticleStatus` |
| Junction tables | `table1_table2` | `articles_tags`, `workspace_members` |

### Schema Blueprint

```sql
-- backend/alembic/versions/ (managed via SQLAlchemy models)
-- SQLAlchemy 2.0 declarative models define the schema.
-- Alembic generates migrations from model changes.

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

# User model example (Phase 2+):
# class User(Base):
#     __tablename__ = "users"
#     id = Column(String, primary_key=True, default=uuid4_str)
#     email = Column(String, unique=True, nullable=False)
#     password_hash = Column("password_hash", String, nullable=False)
#     display_name = Column("display_name", String, nullable=False)
#     created_at = Column("created_at", DateTime, default=func.now())
```

-- See backend/app/infrastructure/models/ for SQLAlchemy 2.0 declarative model definitions
```

---

## 17. Environment Configuration Strategy

### File Hierarchy

```
1. .env.defaults       (committed, team-shared defaults)
2. .env.{stage}        (committed, per-environment defaults)
3. .env.local          (gitignored, developer overrides)
4. process.env         (container/CI injection — highest priority)

Overlay order: 1 < 2 < 3 < 4
```

### Naming Convention

All application-specific environment variables are prefixed with `APP_`:

| Variable | Example | Stage |
|---|---|---|
| `APP_DATABASE_URL` | `postgresql://user:pass@host:5432/db` | All |
| `APP_REDIS_URL` | `redis://host:6379` | All |
| `APP_QDRANT_URL` | `http://host:6333` | All |
| `APP_LOG_LEVEL` | `info` | All |
| `APP_CORS_ORIGINS` | `http://localhost:3000` | Development |
| `APP_JWT_SECRET` | (auto-generated) | Production |
| `APP_ENCRYPTION_KEY` | (auto-generated) | Production |
| `APP_OPENAI_API_KEY` | `sk-...` | Production |
| `APP_OTLP_ENDPOINT` | `http://otel-collector:4318` | Production |
| `APP_RATE_LIMIT_TTL` | `60` | All |
| `APP_RATE_LIMIT_MAX` | `100` | All |

### Validation

On application startup, Pydantic Settings validates the environment. Invalid or missing required variables cause a **hard crash** with a descriptive error message listing all violations:

```python
# backend/app/core/config.py — Pydantic Settings validates on instantiation
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://..."
    REDIS_URL: str = "redis://localhost:6379"
    JWT_SECRET: str = "change-me"
    LOG_LEVEL: str = "INFO"

settings = Settings()  # crashes at import if invalid
```

---

## 18. Multi-Agent Contract Standards

### Agent Request Envelope

```json
{
  "agentId": "agent_classifier_001",
  "model": "gpt-4o-2024-08-06",
  "promptTemplate": "classify_article_v2",
  "promptVariables": {
    "title": "...",
    "body": "...",
    "maxCategories": 5
  },
  "context": {
    "workspaceId": "ws_abc",
    "correlationId": "corr-uuid",
    "jobId": "job_123"
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "categories": { "type": "array", "items": { "type": "string" } },
      "confidence": { "type": "number" }
    },
    "required": ["categories"]
  },
  "config": {
    "temperature": 0.1,
    "maxTokens": 1000,
    "timeoutMs": 30000
  }
}
```

### Agent Response Envelope

```json
{
  "agentId": "agent_classifier_001",
  "status": "success",
  "rawOutput": "... original LLM response text ...",
  "parsedOutput": {
    "categories": ["technology", "AI"],
    "confidence": 0.92
  },
  "usage": {
    "promptTokens": 450,
    "completionTokens": 120,
    "totalTokens": 570
  },
  "latencyMs": 2340,
  "model": "gpt-4o-2024-08-06",
  "error": null
}
```

### Error Response

```json
{
  "agentId": "agent_classifier_001",
  "status": "error",
  "rawOutput": null,
  "parsedOutput": null,
  "usage": null,
  "latencyMs": 30000,
  "model": "gpt-4o-2024-08-06",
  "error": {
    "code": "TIMEOUT",
    "message": "LLM call exceeded timeout of 30000ms",
    "retryable": true
  }
}
```

### Error Classification

| Error Code | Retryable | Description |
|---|---|---|
| `TIMEOUT` | Yes | LLM call exceeded configured timeoutMs |
| `RATE_LIMITED` | Yes | Provider rate limit hit (429) |
| `UNAVAILABLE` | Yes | Provider returned 503 |
| `BAD_REQUEST` | No | Malformed prompt (400 from provider) |
| `AUTH_ERROR` | No | Invalid API key (401/403) |
| `CONTENT_FILTERED` | No | Provider content filter triggered |
| `PARSE_ERROR` | No | LLM output did not match outputSchema |
| `TOKEN_LIMIT` | No (retry with smaller context) | Context + response exceeds model limit |

### Agent Contract Lifecycle

1. **Prompt templates** are versioned in `backend/app/domains/agent/prompts/` (Phase 2+)
2. **Output schemas** are defined as Pydantic models in `backend/app/schemas/analysis/` (Phase 2+)
3. **Agent configurations** (model, temperature, timeout) are stored in the database per workspace
4. **Available agents** are registered at startup via a provider registry pattern

---

## 19. Retry Architecture Standards

### Strategy: Exponential Backoff with Full Jitter

```
delay(attempt) = min(cap, baseDelay * 2^attempt) * random(0.5, 1.5)
```

| Parameter | Default | Configurable |
|---|---|---|
| `baseDelay` | 1000ms | Per operation type |
| `maxDelay` | 60000ms | Global maximum |
| `maxRetries` | 3 | Per operation type |
| `jitterFactor` | 0.5 | Fixed |

### Retry Decision Matrix

| Scenario | Strategy | Max Retries |
|---|---|---|
| Database connection failure | Exponential backoff + jitter | 5 |
| LLM provider 429/503 | Exponential backoff + jitter | 3 |
| LLM provider 5xx (non-503) | Exponential backoff + jitter | 3 |
| HTTP API call to internal service | Exponential backoff + jitter | 2 |
| Event publishing failure | Immediate retry × 1, then dead-letter | 1 |
| State machine transition conflict (409) | Immediate retry with fresh read | 3 |
| SQLAlchemy connection pool timeout | Exponential backoff + jitter | 5 |

### Implementation

```python
# backend/app/core/retry.py (Phase 2+)
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")

@dataclass
class RetryConfig:
    max_attempts: int = 3        # including first attempt
    base_delay_ms: int = 1000
    max_delay_ms: int = 60000
    retryable_errors: list[str] | None = None  # error code whitelist
    timeout_ms: int = 30000      # per-attempt timeout

# Provided as a decorator @retryable(config) and utility
# async def with_retry(fn: Callable[..., Awaitable[T]], config: RetryConfig) -> T
```

### Dead-Letter Policy

When `maxRetries` is exhausted:
1. The operation is recorded in a `dead_letter_queue` table
2. A `system.operation.dead.lettered.v1` event is emitted
3. An alert is fired (severity based on operation criticality)
4. Manual intervention or a separate dead-letter consumer can replay

---

## 20. Validation Architecture Standards

### Validation Boundaries

```mermaid
graph LR
    subgraph "Layer 1: Transport"
        A[HTTP Request] --> B[Pydantic Validation (FastAPI)]
    end
    subgraph "Layer 2: Application"
        B --> C[Service Layer]
        C --> D[Domain Service]
    end
    subgraph "Layer 3: Domain"
        D --> E[Entity Factory]
        E --> F{Invariant Checks}
    end
    subgraph "Layer 4: Egress"
        F --> G[Output Sanitization]
        G --> H[Response]
    end
```

### Layer 1 — Transport Validation (Fail-Fast)

| Concern | Mechanism | Location |
|---|---|---|
| Request body shape | Pydantic model (FastAPI `Depends()`) | Route handler parameter type annotation |
| Request query params | Pydantic model (`Query()`) | Route handler parameter type annotation |
| Path params | FastAPI `Path()` with type validation | Route handler parameter |
| Headers | Pydantic model (`Header()`) | Route handler parameter type annotation |
| Content-Type | FastAPI / Starlette built-in | Framework level |

**Rule:** Every public endpoint MUST have a Pydantic model for its request body. Any endpoint without validation is rejected in code review.

### Layer 2 — Application Validation

| Concern | Mechanism | Location |
|---|---|---|
| Authorization | FastAPI `Depends(get_current_user)` + role check | Route handler or global dependency |
| Idempotency | Redis-backed idempotency key via custom dependency | Route handler |
| Rate limiting | SlowAPI or custom Redis-backed rate limiter dependency | Route handler or global dependency |
| Resource ownership | Custom dependency or service check | Service layer |
| Business rule preconditions | Explicit guard clauses | Service before domain call |

### Layer 3 — Domain Invariant Validation

```python
# Example: domain entity factory with guard clauses
from dataclasses import dataclass

@dataclass
class Article:
    id: str
    title: str
    status: str  # WorkflowStage

    @classmethod
    def create(cls, id: str, title: str, slug: str) -> "Article":
        # Guard clauses — protect domain invariants
        if not title or len(title.strip()) < 3:
            raise DomainException("TITLE_TOO_SHORT", "Title must be at least 3 characters")
        if len(title) > 200:
            raise DomainException("TITLE_TOO_LONG", "Title must not exceed 200 characters")
        if not _is_valid_slug(slug):
            raise DomainException("INVALID_SLUG", "Slug must contain only lowercase letters, numbers, and hyphens")

        return cls(id=id, title=title.strip(), status="INIT")
```

### Layer 4 — Output Sanitization

| Concern | Mechanism |
|---|---|
| Response serialization | Pydantic model `response_model` (strip unknown fields automatically) |
| PII masking | Custom sanitizer for configured fields (email, phone) |
| Null/undefined stripping | Pydantic `exclude_none=True` on response model |
| Pagination limits | Pydantic validator clamps page size to `[1, 100]` |

---

## 21. Observability Architecture Standards

### Three Pillars

```mermaid
graph TD
    subgraph "Application Instrumentation"
        A[OpenTelemetry SDK] --> B[Metrics]
        A --> C[Traces]
        A --> D[Logs]
    end
    subgraph "Collection"
        B --> E[Prometheus]
        C --> F[OTLP Collector]
        D --> F
    end
    subgraph "Visualization"
        E --> G[Grafana]
        F --> H[Jaeger / Tempo]
        D --> I[Loki]
    end
```

### Metrics — RED Pattern

Every service exports the following metrics for each logical operation:

| Metric | Type | Labels | Description |
|---|---|---|---|
| `requests_total` | Counter | `service`, `operation`, `status_code` | Total request count |
| `requests_active` | Gauge | `service`, `operation` | Currently in-flight requests |
| `request_duration_ms` | Histogram | `service`, `operation`, `status_code` | Request latency distribution (buckets: 10, 50, 100, 250, 500, 1000, 2500, 5000, 10000) |
| `errors_total` | Counter | `service`, `operation`, `error_code` | Error count by error code |
| `job_duration_seconds` | Histogram | `service`, `job_type`, `status` | Job execution time |

### Traces — OpenTelemetry

| Instrumentation | Details |
|---|---|
| Propagation | W3C Trace Context (`traceparent`/`tracestate`) |
| Sampling | Probability sampler: 100% dev, 5% prod (head-based) |
| Export | OTLP via gRPC to OpenTelemetry Collector |
| Auto-instrumentation | FastAPI middleware, HTTPX, SQLAlchemy, Redis |
| Manual instrumentation | Key business operations: agent calls, state transitions, saga steps |
| Span attributes | `correlation.id`, `job.id`, `workspace.id`, `user.id` |

### Health Check Endpoints

| Endpoint | Purpose | Required Dependencies |
|---|---|---|
| `GET /v1/health/live` | Kubernetes liveness probe | None (process is alive) |
| `GET /v1/health/ready` | Kubernetes readiness probe | Database, Redis, Qdrant (connection check) |
| `GET /v1/health/startup` | Kubernetes startup probe | Migrations run, cache warm |

### Dashboard Specifications (Grafana)

| Dashboard | Panels |
|---|---|
| **System Health** | CPU/Mem per service, DB connections, Redis hit rate, Event bus lag |
| **API Gateway** | Request rate by route, P50/P95/P99 latency, Error rate by status code, Rate limit breaches |
| **Agent Performance** | Calls per model, Token burn rate, Avg latency per agent, Error rate by error code, Cost per workspace |
| **Workflow Engine** | Job throughput, State transition histogram, Retry rate, Dead-letter count, Avg job duration |
| **Business** | Content items ingested, Insights generated, Active users, Jobs per workspace |

### Alert Rules (Prometheus)

| Alert | Condition | Severity |
|---|---|---|
| `ApiErrorRateHigh` | `errors_total / requests_total > 0.05` for 5m | Critical |
| `ApiLatencyHigh` | `p99_request_duration_ms > 5000` for 5m | Warning |
| `AgentFailureRateHigh` | `agent_errors_total / agent_requests_total > 0.10` for 5m | Critical |
| `JobFailureRateHigh` | `jobs_failed_total / jobs_completed_total > 0.10` for 15m | Critical |
| `DbConnectionPoolExhausted` | `db_pool_available == 0` | Critical |
| `DeadLetterQueueGrowing` | `dead_letter_queue_size > 100` | Warning |

---

## 22. System Context Diagram

```mermaid
graph TB
    subgraph "Browser"
        WEB[Next.js App]
    end

    subgraph "Docker / Kubernetes Cluster"
        subgraph "Applications"
            API[FastAPI API Gateway\nPort 8000]
            WORKER[FastAPI Workers (Celery/Arq)\nPort 8001]
        end

        subgraph "Data Stores"
            PG[(PostgreSQL\nPort 5432)]
            RD[(Redis\nPort 6379)]
            QD[(Qdrant\nPort 6333)]
        end

        subgraph "Observability"
            OTEL[OTel Collector\nPort 4318]
            PROM[Prometheus\nPort 9090]
        end
    end

    subgraph "External"
        LLM1[OpenAI API]
        LLM2[Anthropic API]
        OAUTH[OAuth Provider\nGoogle / GitHub]
    end

    WEB -->|HTTP/REST| API
    WEB -->|WebSocket| API
    API -->|Async Jobs| WORKER
    WORKER --> PG
    WORKER --> RD
    WORKER --> QD
    API --> PG
    API --> RD
    API --> LLM1
    API --> LLM2
    WORKER --> LLM1
    WORKER --> LLM2
    API --> OAUTH
    API --> OTEL
    WORKER --> OTEL
    OTEL --> PROM
    
    classDef external fill:#f9f,stroke:#333,stroke-width:2px;
    class LLM1,LLM2,OAUTH external;
```

---

## Appendix A: Build and Run Commands

```bash
# ── Development ──────────────────────────────────────
cd backend && pip install -r requirements.txt  # Install backend dependencies
cd frontend && npm install                      # Install frontend dependencies
make dev                                        # Start both backend (uvicorn) and frontend (next dev)

# ── Quality ──────────────────────────────────────────
cd backend && ruff check .                      # Lint backend
cd backend && pytest                             # Test backend
cd frontend && npm run lint                      # Lint frontend
cd frontend && npm run typecheck                 # TypeScript strict check

# ── Database ─────────────────────────────────────────
cd backend && alembic upgrade head               # Run migrations

# ── Docker ───────────────────────────────────────────
docker compose -f docker/dev/docker-compose.yml up -d
cd backend && alembic upgrade head
make dev
```

## Appendix B: Dependency Graph

```
# No shared packages or @platform/* / @ai/* conventions.
# Each project (backend, frontend) manages its own dependencies independently.
# Cross-project contracts use OpenAPI 3.1 as the single source of truth.

backend/app/                     (Python 3.11 + FastAPI)
  ├── core/                      (config, logging, db — no internal deps)
  ├── middleware/                (core)
  ├── api/v1/                    (core, schemas)
  ├── schemas/                   (pydantic — no internal deps)
  ├── domains/content/           (infrastructure, domain)
  ├── domains/workflow/          (infrastructure, domain, content)
  ├── domains/analysis/          (infrastructure, domain, workflow, content)
  └── domains/agent/             (infrastructure, domain)

frontend/src/                    (TypeScript + Next.js)
  ├── app/                       (pages routing)
  ├── components/ui/             (shadcn/ui — no internal deps)
  ├── lib/                       (api-client, websocket)
  ├── hooks/                     (shared hooks)
  ├── providers/                 (context providers)
  ├── stores/                    (zustand)
  └── types/                     (generated from OpenAPI)
```

---

*This Architectural Constitution is the governing document for all Phase 1+ development. Every pull request, every module, every endpoint must conform to the standards herein. No exceptions without architecture board approval.*
