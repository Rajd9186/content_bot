# AI Content Intelligence Platform — Phase 1 Foundation

Production-grade infrastructure foundation for a multi-agent content intelligence platform.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Frontend | Next.js 14 App Router (TypeScript) |
| UI | Tailwind CSS + shadcn/ui |
| Database | PostgreSQL + SQLAlchemy (async) |
| Cache / Pub-Sub | Redis |
| Vector Store | Qdrant |
| Observability | OpenTelemetry + Prometheus + Grafana |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Make (optional)

### Full Stack (Docker)

```bash
# Build and start all services
make build
make up

# Services:
# - Frontend:  http://localhost:3000
# - Backend:   http://localhost:8000
# - API Docs:  http://localhost:8000/api/v1/docs
# - Postgres:  localhost:5432
# - Redis:     localhost:6379
# - Qdrant:    localhost:6333
```

### Local Development

```bash
# 1. Start infrastructure
make dev-db

# 2. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
backend/
  app/
    core/           Config, logging, database, exceptions
    api/v1/         Versioned API endpoints
    middleware/     Correlation ID, request logging, error handling
    schemas/        Pydantic models
  tests/
  Dockerfile

frontend/
  src/
    app/            Next.js App Router pages
    components/     UI components + shadcn/ui
    lib/            API client, WebSocket, utilities
    hooks/          React hooks
    providers/      Auth provider context
    stores/         Zustand stores
    types/          TypeScript type definitions
  Dockerfile

docker/
  dev/              Development Docker Compose
  prod/             Production Docker Compose

.github/workflows/  CI/CD pipelines
```

## Quality

```bash
make lint        # Ruff + ESLint
make format      # Ruff + Prettier
make test        # Pytest + Jest
make typecheck   # Pyright + tsc
```

## Architecture

See [ARCHITECTURE_PHASE_0.md](./ARCHITECTURE_PHASE_0.md) for the full architectural constitution.
