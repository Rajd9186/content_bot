
import os
import sys
import importlib
import inspect
from sqlalchemy import create_engine, inspect as sqla_inspect
from app.core.config import settings

def check_circular_imports():
    print("--- Checking for Circular Imports ---")
    # Simulation of importing main modules
    modules = [
        "app.main",
        "app.orchestration.orchestrator",
        "app.domains.workflow.service",
        "app.agents.pipeline",
        "app.db.models.workflow"
    ]
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"[OK] {mod} imported successfully.")
        except ImportError as e:
            print(f"[FAIL] Circular import or failure in {mod}: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to import {mod}: {e}")

def validate_db_schema():
    print("\n--- Validating Database Schema ---")
    try:
        # Use sync driver for inspection
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_url)
        inspector = sqla_inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            "workflow_jobs", "workflow_steps", "execution_logs", 
            "content_items", "content_versions", "generated_content",
            "events", "telemetry_records"
        ]
        
        for table in required_tables:
            if table in tables:
                print(f"[OK] Table '{table}' exists.")
                columns = [c['name'] for c in inspector.get_columns(table)]
                print(f"   Columns: {', '.join(columns[:5])}...")
            else:
                print(f"[FAIL] Table '{table}' is MISSING.")
    except Exception as e:
        print(f"[ERROR] DB Connection failed: {e}")

if __name__ == "__main__":
    check_circular_imports()
    validate_db_schema()
