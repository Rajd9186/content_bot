# Architecture Document

## System Overview

The Verified AI Research Writer is a multi-agent system that produces fact-checked, evidence-backed content. Each stage of the pipeline is handled by a specialized AI agent with structured prompts and outputs.

## Multi-Agent Pipeline

```
┌──────────────┐
│  User Input  │  topic, title, points, tone, audience, keywords
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│         1. Topic Planner            │
│  - Creates structured outline       │
│  - Generates research queries       │
│  - Identifies key sections          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         2. Research Agent           │
│  - Searches web via Tavily API      │
│  - Filters trusted domains          │
│  - Extracts snippets & metadata     │
│  - Computes trust scores            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      3. Verification Agent         │
│  - Extracts factual claims         │
│  - Cross-references evidence       │
│  - Assigns confidence scores       │
│  - Detects contradictions          │
│  - Categorizes claims              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      4. Content Writer Agent       │
│  - Uses ONLY verified claims        │
│  - Produces structured markdown     │
│  - Adds inline citations            │
│  - SEO-optimized formatting         │
│  - Target audience adaptation       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    5. Self-Verification Agent      │
│  - Audits for hallucination risks   │
│  - Detects unsupported claims       │
│  - Finds internal contradictions    │
│  - Adjusts confidence scores        │
│  - Generates final quality report   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     6. Verification Dashboard      │
│  - Displays all results             │
│  - Shows trust metrics              │
│  - Highlights issues                │
│  - Provides evidence trail          │
└─────────────────────────────────────┘
```

## Data Flow

### Request Flow
1. User submits content parameters via frontend form
2. Frontend creates project via POST /api/v1/projects
3. Frontend triggers generation via POST /api/v1/projects/{id}/generate
4. Backend orchestrates the 5-agent pipeline
5. Results persisted to SQLite at each stage
6. Frontend polls for status updates
7. On completion, frontend renders verification dashboard

### Database Schema

```
projects
├── id (UUID, PK)
├── topic, title, points_to_cover (JSONB)
├── tone, content_type, target_audience
├── seo_keywords (JSONB), status, outline (JSONB)
├── created_at, updated_at
│
├── generated_content (1+)
│   ├── id, project_id (FK)
│   ├── markdown, summary, word_count
│   ├── citations (JSONB), seo_metadata (JSONB)
│   └── overall_confidence, created_at
│
├── claims (1+)
│   ├── id, project_id (FK)
│   ├── claim_text, confidence, status
│   ├── explanation, category
│   └── created_at
│
├── evidence (1+)
│   ├── id, project_id (FK), claim_id (FK)
│   ├── source_id (FK)
│   ├── snippet, relevance_score
│   └── extracted_at
│
└── sources (1+)
    ├── id, project_id (FK)
    ├── url, domain, title
    ├── trust_score, author
    ├── published_date, snippet
    └── created_at
```

## Trust Scoring System

| Domain Pattern | Base Trust Score |
|---------------|------------------|
| reuters.com   | 0.95             |
| nasa.gov      | 0.95             |
| nih.gov       | 0.94             |
| cdc.gov       | 0.93             |
| who.int       | 0.93             |
| worldbank.org | 0.92             |
| nature.com    | 0.92             |
| imf.org       | 0.92             |
| science.org   | 0.91             |
| *.gov         | 0.90             |
| *.edu         | 0.85             |
| Default       | 0.60             |

## Claim Confidence

- **Verified** (>0.85): Direct supporting evidence from high-trust sources
- **Unverified** (0.70-0.85): Some evidence but not conclusive
- **Contradicted**: Evidence directly contradicts the claim
- **Unsupported** (<0.70): No evidence found

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/projects | Create project |
| GET | /api/v1/projects | List projects |
| GET | /api/v1/projects/{id} | Get project |
| DELETE | /api/v1/projects/{id} | Delete project |
| GET | /api/v1/projects/{id}/content | Get content |
| GET | /api/v1/projects/{id}/content/latest | Get latest content |
| POST | /api/v1/projects/{id}/content/generate | Generate content |
| GET | /api/v1/projects/{id}/evidence | Get evidence |
| GET | /api/v1/projects/{id}/evidence/claims/{claim_id} | Get evidence by claim |
| GET | /api/v1/projects/{id}/verification/claims | Get verification results |
| GET | /api/v1/projects/{id}/verification/sources | Get source trust metrics |
| GET | /api/v1/projects/{id}/verification/dashboard | Get full dashboard |

## Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, TailwindCSS
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy async
- **Database**: SQLite via aiosqlite
- **AI**: Ollama (e.g., nemotron-3-super:cloud)
- **Search**: Tavily API
- **Infrastructure**: Docker, Docker Compose

## Security

- API keys stored in environment variables
- CORS restricted to frontend origin
- SQLAlchemy parameterized queries (no SQL injection)
- Input validation via Pydantic v2
- No secrets in codebase
