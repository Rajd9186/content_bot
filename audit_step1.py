
import os
import sys
import importlib
import json
from datetime import datetime

# Setup paths
PROJECT_ROOT = os.getcwd()
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.append(BACKEND_DIR)

REPORT = {
    "timestamp": datetime.now().isoformat(),
    "step": "STEP 1: Project Structure & Architecture",
    "findings": [],
    "critical_issues": [],
    "metrics": {
        "duplicate_systems": 0,
        "circular_imports": 0,
        "dead_code_files": 0
    }
}

def audit_structure():
    print("--- Auditing Architecture Consistency ---")
    
    # Check for duplicate orchestration
    orch_engine = os.path.exists(os.path.join(BACKEND_DIR, "app/orchestration"))
    workflow_domain = os.path.exists(os.path.join(BACKEND_DIR, "app/domains/workflow"))
    
    if orch_engine and workflow_domain:
        REPORT["findings"].append({
            "type": "DUPLICATE_SYSTEM",
            "description": "Both app/orchestration and app/domains/workflow exist. Risk: Split brain orchestration logic.",
            "severity": "HIGH"
        })
        REPORT["metrics"]["duplicate_systems"] += 1

    # Check for duplicate model roots
    db_models = os.path.exists(os.path.join(BACKEND_DIR, "app/db/models"))
    infra_models = os.path.exists(os.path.join(BACKEND_DIR, "app/infrastructure/models"))
    
    if db_models and infra_models:
        REPORT["findings"].append({
            "type": "REDUNDANT_MODELS",
            "description": "Models split between app/db/models and app/infrastructure/models. Risk: Migration/Sync issues.",
            "severity": "MEDIUM"
        })

    # Check for circular imports using importlib
    modules_to_test = [
        "app.main",
        "app.domains.workflow.models",
        "app.infrastructure.unit_of_work",
        "app.events.event_bus"
    ]
    
    for mod_name in modules_to_test:
        try:
            importlib.import_module(mod_name)
            print(f"[OK] {mod_name} imported.")
        except ImportError as e:
            if "partially initialized" in str(e):
                REPORT["critical_issues"].append(f"CIRCULAR_IMPORT: {mod_name} -> {e}")
                REPORT["metrics"]["circular_imports"] += 1
            else:
                REPORT["findings"].append(f"IMPORT_ERROR: {mod_name} -> {e}")

    # Dead code check (Orphaned files)
    # Check for v1/v2/v3 naming in files
    for root, dirs, files in os.walk(BACKEND_DIR):
        for file in files:
            if any(v in file.lower() for v in ["v1", "v2", "v3", "old", "bak"]):
                if "api/v1" not in root: # Ignore legitimate versioned APIs
                    REPORT["findings"].append({
                        "type": "POTENTIAL_DEAD_CODE",
                        "path": os.path.join(root, file),
                        "description": "Versioned or backup file found in active tree."
                    })

def generate_report():
    print(json.dumps(REPORT, indent=2))
    with open("audit_step1_report.json", "w") as f:
        json.dump(REPORT, f, indent=2)

if __name__ == "__main__":
    audit_structure()
    generate_report()
