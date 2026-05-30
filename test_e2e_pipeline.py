
import asyncio
import json
import uuid
import sys
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_end_to_end_pipeline():
    print("--- Starting End-to-End Content Pipeline Validation ---")
    
    from app.pipeline.graph import pipeline
    from app.pipeline.state import PipelineState, ReviewAction
    
    workflow_id = str(uuid.uuid4())
    state = PipelineState(
        workflow_id=workflow_id,
        workspace_id="test-workspace",
        correlation_id=str(uuid.uuid4()),
        topic="The Future of Agentic AI in Enterprise",
        audience="CTOs and Architects",
        tone="professional",
        goals="Explain why goose is the best agent",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    
    print(f"Workflow ID: {workflow_id}")
    print("Running Research, Planning, and Writing stages...")
    
    try:
        # We use skip_human_review=True to run through the automated parts
        final_state = await pipeline.execute(state, skip_human_review=True)
        
        print(f"Current Node: {final_state.current_node}")
        print(f"Node Results: {list(final_state.node_results.keys())}")
        
        # Validate content was generated
        if final_state.draft_content and len(final_state.draft_content) > 100:
            print(f"[OK] Content generated successfully ({len(final_state.draft_content)} chars)")
        else:
            print("[FAIL] Content generation produced empty or too short output")
            
        # Validate Research integration
        if final_state.research_data and "summary" in final_state.research_data:
            print(f"[OK] Research data integrated: {final_state.research_data['summary'][:50]}...")
        else:
            print("[FAIL] Research data missing or incomplete")
            
        # Validate SEO integration
        if final_state.seo_metadata and "primary_keywords" in final_state.seo_metadata:
            print(f"[OK] SEO metadata generated: {final_state.seo_metadata['primary_keywords']}")
        else:
            print("[FAIL] SEO metadata missing")
            
        # Validate Terminal State
        if final_state.all_nodes_completed():
             print("[OK] All nodes marked as completed")
        else:
             print(f"[WARNING] Not all nodes completed. Failures: {final_state.errors}")

    except Exception as e:
        print(f"[CRITICAL] Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_end_to_end_pipeline())
