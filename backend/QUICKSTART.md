# Quick Start - Local Development

## Prerequisites

1. **Python 3.11+** installed
2. **PostgreSQL** running locally (or update `.env` with your DB URL)
3. **Redis** running locally (optional, for outbox/janitor workers)

## Setup Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already created. Update these values if needed:

```bash
# Database (default: postgresql://postgres:postgres@localhost:5432/ai_content_dev)
APP_DATABASE_URL=postgresql://user:password@localhost:5432/your_db

# Redis (optional)
APP_REDIS_URL=redis://localhost:6379

# API Keys (optional for testing)
OPENAI_API_KEY=your-key-here
```

### 3. Run Database Migrations

```bash
# From backend directory
alembic upgrade head
```

### 4. Start the Application

**Option A: Using uvicorn directly**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: Using Python**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Application

- **API Docs**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **Health Check**: http://localhost:8000/

## Test the Agents

Once running, you can test agents via the API:

```bash
# Example: Test the planner agent
curl -X POST http://localhost:8000/api/v1/orchestration/create \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Artificial Intelligence",
    "goals": "Explain AI concepts",
    "audience": "Beginners"
  }'
```

## Troubleshooting

**Database connection error:**
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE ai_content_dev;"
```

**Redis not running (optional):**
```bash
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Or use Docker: docker run -p 6379:6379 redis:latest
```

**Port already in use:**
```bash
# Change port in the uvicorn command
uvicorn app.main:app --reload --port 8001
```

## Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run agent tests only
pytest tests/agents/ -v
```