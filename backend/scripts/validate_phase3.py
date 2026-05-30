
import os
import sys
import json
import asyncio
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = os.getcwd()
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.append(BACKEND_DIR)

async def validate_orchestration_engine():
    print("--- PHASE 3: ORCHESTRATION ENGINE VALIDATION ---")
    
    # 1. Validate Orchestration Stages (The Stage Machine)
    from app.orchestration.stages import WorkflowStage, WorkflowStatus as OrchStatus, WorkflowRun, validate_transition
    from app.orchestration.state_machine import orchestration_state_machine
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE 3 — ORCHESTRATION ENGINE",
        "tests": []
    }

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

    # Test 2: Workflow Domain State Machine
    from app.domains.workflow.state_machine import WorkflowStatus as DomStatus, workflow_state_machine
    
    domain_path = [
        (DomStatus.DRAFT, DomStatus.QUEUED),
        (DomStatus.QUEUED, DomStatus.VALIDATING),
        (DomStatus.VALIDATING, DomStatus.PROCESSING),
        (DomStatus.PROCESSING, DomStatus.COMPLETED)
    ]
    
    domain_results = []
    for f, t in domain_path:
        # Simplified check - can_transition returns (bool, reason)
        ok, _ = await workflow_state_machine.can_transition(f.value, t.value, "test-job", "test-ws")
        domain_results.append(ok)
        if not ok:
            print(f"Domain State FAILED: {f} -> {t}")

    report["tests"].append({
        "name": "Workflow Domain State Machine Integrity",
        "status": "PASS" if all(domain_results) else "FAIL",
        "details": f"Validated {sum(domain_results)}/{len(domain_results)} domain transitions."
    })

    # Test 3: Illegal Transition Rejection
    illegal = [
        (WorkflowStage.INIT, WorkflowStage.PUBLISHED),
        (WorkflowStage.PUBLISHED, WorkflowStage.RESEARCH)
    ]
    rejection_ok = True
    for f, t in illegal:
        try:
            validate_transition(f, t)
            rejection_ok = False
        except ValueError:
            pass # Expected
            
    report["tests"].append({
        "name": "Illegal Transition Rejection",
        "status": "PASS" if rejection_ok else "FAIL",
        "details": "Correctly blocked jumps and reverse transitions."
    })

    print(json.dumps(report, indent=2))
    with open("phase3_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    asyncio.run(validate_orchestration_engine())
