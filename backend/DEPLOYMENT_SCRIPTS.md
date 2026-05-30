# Production Deployment Script

## Prerequisites Check Script

```powershell
# check-prerequisites.ps1

Write-Host "Checking deployment prerequisites..." -ForegroundColor Cyan

# Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Python not found. Install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
try {
    $pgTest = psql --version 2>&1
    Write-Host "[OK] PostgreSQL client installed" -ForegroundColor Green
} catch {
    Write-Host "[WARN] PostgreSQL client not found. Install if deploying database locally." -ForegroundColor Yellow
}

# Check Redis
try {
    $redisTest = redis-cli --version 2>&1
    Write-Host "[OK] Redis client installed" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Redis client not found. Install if using Redis locally." -ForegroundColor Yellow
}

# Check dependencies
Write-Host "`nChecking Python dependencies..." -ForegroundColor Cyan
$deps = pip list 2>&1 | Select-String -Pattern "fastapi|uvicorn|sqlalchemy|pydantic"
if ($deps) {
    Write-Host "[OK] Core dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[WARN] Some dependencies may be missing. Run: pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host "`nPrerequisites check complete!" -ForegroundColor Cyan
```

---

## Quick Deploy Script

```powershell
# deploy.ps1

param(
    [string]$Environment = "production",
    [string]$Port = "8000",
    [int]$Workers = 2
)

Write-Host "Deploying AI Content Intelligence Platform" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Port: $Port" -ForegroundColor Yellow
Write-Host "Workers: $Workers" -ForegroundColor Yellow

# Set environment
$env:APP_ENVIRONMENT = $Environment
$env:APP_DEBUG = if ($Environment -eq "production") { "false" } else { "true" }

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --upgrade

# Run migrations
Write-Host "`nRunning database migrations..." -ForegroundColor Cyan
alembic upgrade head

# Start application
Write-Host "`nStarting application on port $Port..." -ForegroundColor Green
uvicorn app.main:app `
    --host 0.0.0.0 `
    --port $Port `
    --workers $Workers `
    --reload:(if ($Environment -eq "development") { $true } else { $false })
```

---

## Production Start Script (Linux/Mac)

```bash
#!/bin/bash
# start-production.sh

set -e

echo "Starting AI Content Intelligence Platform in production mode..."

# Environment
export APP_ENVIRONMENT=production
export APP_DEBUG=false
export APP_LOG_LEVEL=INFO

# Install/upgrade dependencies
pip install -r requirements.txt --upgrade

# Run migrations
alembic upgrade head

# Start with gunicorn (recommended for production)
if command -v gunicorn &> /dev/null; then
    echo "Starting with Gunicorn..."
    gunicorn app.main:app \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --timeout 120 \
        --keep-alive 5
else
    echo "Starting with Uvicorn..."
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4
fi
```

---

## Production Start Script (Windows)

```powershell
# start-production.ps1

# Environment
$env:APP_ENVIRONMENT = "production"
$env:APP_DEBUG = "false"
$env:APP_LOG_LEVEL = "INFO"

Write-Host "Starting AI Content Intelligence Platform..." -ForegroundColor Green

# Install dependencies
pip install -r requirements.txt --upgrade

# Run migrations
alembic upgrade head

# Start application
Write-Host "Starting with 4 workers on port 8000..." -ForegroundColor Cyan
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Systemd Service (Linux)

```ini
# /etc/systemd/system/ai-content-backend.service

[Unit]
Description=AI Content Intelligence Platform Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/ai-content/backend
Environment="PATH=/opt/ai-content/venv/bin"
Environment="APP_ENVIRONMENT=production"
Environment="APP_DEBUG=false"
ExecStart=/opt/ai-content/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-content-backend

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-content-backend
sudo systemctl start ai-content-backend
sudo systemctl status ai-content-backend
```

---

## Nginx Reverse Proxy Configuration

```nginx
# /etc/nginx/sites-available/ai-content

upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Logging
    access_log /var/log/nginx/ai-content-access.log;
    error_log /var/log/nginx/ai-content-error.log;

    # Size limits
    client_max_body_size 10M;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # Buffering
        proxy_buffering off;
        proxy_cache off;
    }

    # Health check endpoint
    location /api/v1/health {
        proxy_pass http://backend/api/v1/health;
        access_log off;
    }
}
```

---

## Environment-Specific Configurations

### Development (.env.development)
```bash
APP_ENVIRONMENT=development
APP_DEBUG=true
APP_LOG_LEVEL=DEBUG
APP_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_content_dev
APP_REDIS_URL=redis://localhost:6379
APP_DATABASE_POOL_SIZE=5
APP_DATABASE_MAX_OVERFLOW=10
```

### Staging (.env.staging)
```bash
APP_ENVIRONMENT=staging
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_DATABASE_URL=postgresql+asyncpg://user:pass@staging-db:5432/ai_content_staging
APP_REDIS_URL=redis://staging-redis:6379
APP_DATABASE_POOL_SIZE=10
APP_DATABASE_MAX_OVERFLOW=20
```

### Production (.env.production)
```bash
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_LOG_LEVEL=WARNING
APP_DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/ai_content_prod
APP_REDIS_URL=redis://prod-redis:6379
APP_DATABASE_POOL_SIZE=20
APP_DATABASE_MAX_OVERFLOW=40
APP_DATABASE_ECHO=false
```

---

## Deployment Verification

```powershell
# verify-deployment.ps1

Write-Host "Verifying deployment..." -ForegroundColor Cyan

# Check if app is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 10
    $health = $response.Content | ConvertFrom-Json
    
    if ($health.status -eq "ok") {
        Write-Host "[OK] Application is healthy" -ForegroundColor Green
        Write-Host "  Version: $($health.version)" -ForegroundColor Gray
        Write-Host "  Uptime: $($health.uptimeSeconds)s" -ForegroundColor Gray
    } else {
        Write-Host "[FAIL] Application returned unhealthy status" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[FAIL] Application is not responding" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Check API docs
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/docs" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] API docs accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARN] API docs not accessible" -ForegroundColor Yellow
}

Write-Host "`nDeployment verification complete!" -ForegroundColor Cyan
```

---

## Rollback Script

```powershell
# rollback.ps1

param(
    [string]$PreviousVersion = ""
)

Write-Host "Rolling back deployment..." -ForegroundColor Yellow

if ($PreviousVersion) {
    # Git rollback
    git checkout $PreviousVersion
    
    # Reinstall dependencies
    pip install -r requirements.txt
    
    # Rollback database migrations
    alembic downgrade -1
    
    # Restart service
    Restart-Service ai-content-backend
    
    Write-Host "Rollback to $PreviousVersion complete!" -ForegroundColor Green
} else {
    Write-Host "No previous version specified. Please provide a version tag." -ForegroundColor Red
    exit 1
}
```