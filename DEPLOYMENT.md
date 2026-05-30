# Deployment Guide

## Quick Deployment Options

### Option 1: Docker Compose (Recommended for Local/Dev)

```bash
# Set environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

**Services:**
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

### Option 2: Kubernetes (Production)

```bash
# Create namespace and apply configs
kubectl apply -f k8s-deployment.yaml

# Set secrets
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export POSTGRES_PASSWORD="secure-password"
envsubst < k8s-deployment.yaml | kubectl apply -f -

# Check deployment
kubectl get pods -n ai-content-platform
kubectl get services -n ai-content-platform

# View logs
kubectl logs -f deployment/backend-deployment -n ai-content-platform

# Port forward for local access
kubectl port-forward service/backend-service 8000:80 -n ai-content-platform
```

---

### Option 3: Cloud Deployment

#### AWS (ECS/Fargate)

```bash
# Build and push to ECR
aws ecr create-repository --repository-name ai-content-backend
docker build -t ai-content-backend .
docker tag ai-content-backend:latest <account>.dkr.ecr.region.amazonaws.com/ai-content-backend:latest
docker push <account>.dkr.ecr.region.amazonaws.com/ai-content-backend:latest

# Deploy with AWS CLI
aws ecs create-service --cluster ai-content --service-name backend --task-definition ai-content-backend
```

#### Google Cloud (Cloud Run)

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-content-backend
gcloud run deploy ai-content-backend \
  --image gcr.io/PROJECT_ID/ai-content-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=your-key
```

#### Azure (Container Apps)

```bash
# Deploy to Azure Container Apps
az containerapp up \
  --name ai-content-backend \
  --resource-group my-resource-group \
  --image ai-content-backend:latest \
  --environment my-environment \
  --target-port 8000 \
  --ingress external \
  --env-vars OPENAI_API_KEY=your-key
```

---

### Option 4: Railway/Render/Fly.io (PaaS)

#### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

#### Render

```bash
# Connect GitHub repo and deploy via Render dashboard
# Add environment variables in Render UI
```

#### Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
fly secrets set OPENAI_API_KEY=your-key
```

---

## Environment Variables

### Required
```bash
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
APP_REDIS_URL=redis://host:6379
```

### Optional (AI Providers)
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
```

### Database
```bash
APP_DATABASE_POOL_SIZE=20
APP_DATABASE_MAX_OVERFLOW=40
APP_DATABASE_ECHO=false
```

---

## Database Setup

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Or locally
alembic upgrade head
```

---

## Health Checks

```bash
# API Health
curl http://localhost:8000/api/v1/health

# Expected response
{
  "status": "ok",
  "version": "1.0.0",
  "uptimeSeconds": 123.45
}
```

---

## Monitoring

### Prometheus Metrics (if enabled)
- Endpoint: `/metrics`
- Metrics: request_count, request_latency, agent_executions, token_usage

### Logging
- Format: JSON
- Level: INFO (production), DEBUG (development)
- Correlation ID: Included in all logs

---

## Scaling Recommendations

### Horizontal Scaling
- Backend: 2-10 replicas (auto-scaled)
- PostgreSQL: Read replicas for heavy load
- Redis: Cluster mode for high availability

### Resource Limits
- Backend: 512Mi-1Gi RAM, 500m-1000m CPU per replica
- PostgreSQL: 1-2Gi RAM, 500m-1000m CPU
- Redis: 256-512Mi RAM, 100-200m CPU

---

## Security Checklist

- [ ] Use secrets management (AWS Secrets Manager, GCP Secret Manager)
- [ ] Enable TLS/SSL for all endpoints
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable authentication (if required)
- [ ] Regular security updates
- [ ] Network policies (Kubernetes)
- [ ] Database encryption at rest

---

## Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker-compose exec backend python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### Database migrations fail
```bash
# Reset and re-run
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
```

### High memory usage
```bash
# Reduce pool sizes in .env
APP_DATABASE_POOL_SIZE=10
APP_DATABASE_MAX_OVERFLOW=20
```