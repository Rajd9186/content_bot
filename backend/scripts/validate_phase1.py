import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# Setup paths to ensure we can import the app
PROJECT_ROOT = r"C:\Users\rajde\source\repos\AI Research"
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.append(BACKEND_DIR)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase1Validation")

async def validate_infrastructure():
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE 1 — INFRASTRUCTURE",
        "checks": []
    }

    # 1. Check Configuration & Environment
    try:
        from app.core.config import settings
        results["checks"].append({
            "name": "Environment Loading",
            "status": "PASS",
            "details": f"Project: {settings.PROJECT_NAME}, Version: {settings.VERSION}"
        })
    except Exception as e:
        results["checks"].append({
            "name": "Environment Loading",
            "status": "FAIL",
            "details": str(e)
        })

    # 2. Check Database Schema via SQLAlchemy Inspect
    try:
        from sqlalchemy import create_engine, inspect
        # Using a sync engine for inspection (simplest for validation script)
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            "workflow_jobs", "workflow_steps", "execution_logs", 
            "content_items", "content_versions", "generated_content",
            "stored_events", "retry_records", "telemetry_metrics"
        ]
        
        missing = [t for t in required_tables if t not in tables]
        
        if not missing:
            results["checks"].append({
                "name": "PostgreSQL Schema",
                "status": "PASS",
                "details": f"All {len(required_tables)} core tables present."
            })
        else:
            results["checks"].append({
                "name": "PostgreSQL Schema",
                "status": "FAIL",
                "details": f"Missing tables: {', '.join(missing)}"
            })
    except Exception as e:
        results["checks"].append({
            "name": "PostgreSQL Connectivity",
            "status": "FAIL",
            "details": str(e)
        })

    # 3. Check Redis Connectivity Implementation
    try:
        from app.infrastructure.messaging.redis_client import redis_client
        # We check the code structure/config since we might not have a running redis in this environment
        # but we can verify the URL is set.
        if settings.REDIS_URL:
            results["checks"].append({
                "name": "Redis Configuration",
                "status": "PASS",
                "details": f"Redis URL configured: {settings.REDIS_URL}"
            })
        else:
            results["checks"].append({
                "name": "Redis Configuration",
                "status": "FAIL",
                "details": "REDIS_URL is empty"
            })
    except Exception as e:
        results["checks"].append({
            "name": "Redis Configuration",
            "status": "FAIL",
            "details": str(e)
        })

    # 4. Check API Structure & Startup Logic
    try:
        from app.main import app
        results["checks"].append({
            "name": "FastAPI App Initialization",
            "status": "PASS",
            "details": f"Routes defined: {len(app.routes)}"
        })
    except Exception as e:
        results["checks"].append({
            "name": "FastAPI Startup",
            "status": "FAIL",
            "details": str(e)
        })

    # Write report
    report_path = os.path.join(PROJECT_ROOT, "phase1_health_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    asyncio.run(validate_infrastructure())
