# Verified AI Research Writer

An AI-powered verified content generation platform that produces fact-checked, evidence-backed content with full transparency and trust metrics.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Frontend  │────▶│   Backend    │────▶│  OpenAI    │
│  (Next.js)  │     │  (FastAPI)   │     │  Ollama    │
└─────────────┘     └──────────────┘     └────────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │    SQLite    │
                    └──────────────┘
```

## Multi-Agent Pipeline

```
User Input
    │
    ▼
┌─────────────────┐
│ Topic Planner   │ ──▶ Generate outline & structure
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Research Agent  │ ──▶ Search web, retrieve evidence
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Verification    │ ──▶ Extract claims, verify facts
│ Agent           │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Content Writer  │ ──▶ Generate verified content
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Self-Verifier   │ ──▶ Re-verify, detect contradictions
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Verification    │ ──▶ Display results & trust metrics
│ Dashboard       │
└─────────────────┘
```

## Features (Phase 1)

1. **Content Generation Form** - User provides topic, title, points, tone, audience, SEO keywords
2. **Topic Planning Engine** - AI generates structured outline
3. **Web Research System** - Searches trusted sources via Tavily API
4. **Evidence Retrieval** - Extracts and stores supporting evidence
5. **Claim Extraction** - Identifies factual claims from research
6. **Fact Verification** - Cross-references claims against sources
7. **Source Trust Scoring** - Ranks sources by authority (Reuters: 0.95, SEC: 0.98, .gov: 0.90, .edu: 0.85)
8. **Verified Content Generation** - Writes content using only verified claims
9. **Citation Generation** - Appends inline citations with source metadata
10. **Self-Verification** - Post-generation claim audit
11. **Verification Dashboard** - Confidence scores, contradictions, source metrics
12. **SQLite Persistence** - All data stored with full relationships via SQLAlchemy
13. **FastAPI Backend** - Async Python with Pydantic v2 validation
14. **Next.js Frontend** - TypeScript, TailwindCSS, responsive
15. **Docker Compose** - One-command startup
16. **Structured Logging** - JSON logging with correlation IDs
17. **Multi-Agent Architecture** - Specialized agents with prompt templates

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama API key
- Tavily API key (optional, falls back to mock)

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd Content
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export OLLAMA_API_KEY=your-ollama-key
export TAVILY_API_KEY=your-tavily-key
export SECRET_KEY=your-secret-key
```

4. Run the backend:
```bash
python -m app.main
```

5. (Optional) Run frontend:
```bash
cd frontend
npm install
npm run dev
```

6. Access the application:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects` | Create a new project |
| GET | `/api/v1/projects/{id}` | Retrieve project details |
| POST | `/api/v1/projects/{id}/generate` | Generate content for project |
| GET | `/api/v1/projects/{id}/content` | Get generated content |
| GET | `/api/v1/projects/{id}/evidence` | Get evidence sources |
| GET | `/api/v1/projects/{id}/verification` | Get verification results |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/         # AI agents (planner, researcher, verifier, writer)
│   │   ├── log_config/     # Structured JSON logging
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── repositories/   # Data access layer
│   │   ├── routes/         # FastAPI route handlers
│   │   ├── schemas/        # Pydantic v2 schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helpers & retry logic
│   ├── alembic/            # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages
│   │   ├── components/     # React components
│   │   ├── lib/            # API client
│   │   └── types/          # TypeScript types
│   └── Dockerfile
├── docs/
└── docker-compose.yml
```

## Trusted Sources

The system prioritizes evidence from:
- **Reuters** (trust score: 0.95)
- **SEC.gov** (trust score: 0.98)
- **Government domains** (.gov, trust score: 0.90)
- **Educational institutions** (.edu, trust score: 0.85)
- **Major news outlets** (trust score: 0.80)
- **Industry publications** (trust score: 0.70)
