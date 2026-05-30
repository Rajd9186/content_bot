import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone

# Setup paths to ensure we can import the app
PROJECT_ROOT = os.getcwd()
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.append(BACKEND_DIR)

# Configure logging to see import issues clearly
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Phase3Validation")

async def validate_orchestration_engine():
    print("--- PHASE 3: ORCHESTRATION ENGINE VALIDATION (Isolated) ---")
    
    # We will try to import the domain models and state machine without using the full registry
    # to bypass the circular dependency in this test script if possible.
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE 3 — ORCHESTRATION ENGINE",
        "tests": []
    }

    try:
        from app.orchestration.stages import WorkflowStage, validate_transition
        
        # Test 1: Stage Transition Linear Integrity
        linear_stages = [
            (WorkflowStage.INIT, WorkflowStage.PLANNING),
            (WorkflowStage.PLANNING, WorkflowStage.RESEARCH),
            (WorkflowStage.RESEARCH, WorkflowStage.SYNTHESIS),
            (WorkflowStage.SYNTHESIS, WorkflowStage.OUTLINING),
            (WorkflowStage.OUTLINING, WorkflowStage.WRITING),
            (WorkflowStage.WRITING, WorkflowStage.VALIDATION),
            (WorkflowStage.VALIDATION, WorkflowStage.SEO),
            (WorkflowStage.SEO, WorkflowStage.FACT_CHECK),
            (WorkflowStage.FACT_CHECK, WorkflowStage.FINALIZATION),
            (WorkflowStage.FINALIZATION, WorkflowStage.PUBLISHED)
        ]
        
        stage_results = []
        for f, t in linear_stages:
            try:
                validate_transition(f, t)
                stage_results.append(True)
            except Exception as e:
                print(f"Orch Stage FAILED: {f} -> {t}: {e}")
                stage_results.append(False)
                
        report["tests"].append({
            "name": "Orchestration Stage Path Integrity",
            "status": "PASS" if all(stage_results) else "FAIL",
            "details": f"Validated {sum(stage_results)}/{len(linear_stages)} transitions."
        })
    except Exception as e:
        report["tests"].append({
            "name": "Orchestration Stage Path Integrity",
            "status": "FAIL",
            "details": f"Import error: {str(e)}"
        })

    try:
        from app.domains.workflow.state_machine import WorkflowStatus, workflow_state_machine
        
        # Test 2: Workflow Domain State Machine Integrity
        domain_path = [
            (WorkflowStatus.DRAFT, WorkflowStatus.QUEUED),
            (WorkflowStatus.QUEUED, WorkflowStatus.VALIDATING),
            (WorkflowStatus.VALIDATING, WorkflowStatus.PROCESSING),
            (WorkflowStatus.PROCESSING, WorkflowStatus.COMPLETED)
        ]
        
        domain_results = []
        for f, t in domain_path:
            ok, _ = await workflow_state_machine.can_transition(f.value, t.value, "test-job", "test-ws")
            domain_results.append(ok)
            if not ok:
                print(f"Domain State FAILED: {f} -> {t}")

        report["tests"].append({
            "name": "Workflow Domain State Machine Integrity",
            "status": "PASS" if all(domain_results) else "FAIL",
            "details": f"Validated {sum(domain_results)}/{len(domain_results)} domain transitions."
        })
    except Exception as e:
         report["tests"].append({
            "name": "Workflow Domain State Machine Integrity",
            "status": "FAIL",
            "details": f"Import/Execution error: {str(e)}"
        })

    # Output report
    print(json.dumps(report, indent=2))
    with open("phase3_validation_report_final.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    asyncio.run(validate_orchestration_engine())
