
import asyncio
import json
import uuid
import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_end_to_end_pipeline_mocked():
    print("--- Starting End-to-End Content Pipeline Validation (Mocked LLM) ---")
    
    from app.pipeline.graph import pipeline
    from app.pipeline.state import PipelineState, ReviewAction
    from app.agents.provider.factory import provider_factory
    from app.agents.provider.base import ProviderResponse
    from app.agents.contracts import TokenUsage
    
    # Mock Responses for all agents
    mock_responses = {
        "research": {
            "summary": "Deep research into Agentic AI for enterprise.",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "statistics": ["80% of enterprises..."],
            "citations": ["Source A", "Source B"],
            "entities": ["AI Agent", "Enterprise"],
            "risks": ["Risk X"],
            "outline_suggestions": ["Intro", "Body", "Conclusion"],
            "gaps": ["Gap Y"],
            "contradictions": ["None"]
        },
        "planner": {
            "title": "Agentic AI in Enterprise",
            "sections": [
                {"title": "Introduction", "key_points": ["What is it?"]},
                {"title": "Core Benefits", "key_points": ["Efficiency", "Cost"]}
            ],
            "goals": ["Educate"],
            "target_audience": ["CTOs"],
            "key_themes": ["AI", "Enterprise"],
            "research_questions": ["How?"],
            "success_criteria": ["Readability"],
            "estimated_word_count": 1000
        },
        "writer": {
            "content": "# Agentic AI\n\nFull article body here with more than 100 characters to pass validation.",
            "title": "Agentic AI",
            "word_count": 1000,
            "sections_written": ["Intro", "Body"],
            "citations_used": ["Source A"]
        },
        "seo": {
            "title": "Optimized AI",
            "meta_description": "SEO Desc",
            "url_slug": "agentic-ai",
            "primary_keywords": ["AI", "Enterprise"],
            "secondary_keywords": ["Goose"],
            "heading_suggestions": ["New Headings"],
            "internal_links": [],
            "external_links": [],
            "readability_score": 80,
            "word_count_target": 1000,
            "content": "# Optimized Agentic AI\n\nSEO content."
        },
        "fact_checker": {
            "verified_claims": ["Claim 1"],
            "unverified_claims": [],
            "disputed_claims": [],
            "corrections": [],
            "overall_assessment": "Good",
            "confidence_score": 0.95,
            "content": "# Verified Content"
        },
        "compliance": {
            "compliance_status": "pass",
            "issues": [],
            "disclaimers_needed": [],
            "brand_safety_score": 100,
            "regulatory_checks": ["GDPR"],
            "overall_verdict": "Safe",
            "content": "# Compliant Content"
        },
        "finalizer": {
            "final_content": "# Final Agentic AI Content\n\nThis is the end-to-end result.",
            "title": "Final Title",
            "excerpt": "Excerpt",
            "word_count": 1000,
            "reading_time_minutes": 5,
            "metadata": {},
            "citations_list": [],
            "change_log": []
        }
    }

    # Helper to create successful ProviderResponse
    def create_mock_resp(content_dict):
        return ProviderResponse(
            success=True,
            content=json.dumps(content_dict),
            token_usage=TokenUsage(total_tokens=100, prompt_tokens=50, completion_tokens=50, provider="mock", model="mock"),
            latency_ms=10,
            provider="mock",
            model="mock"
        )

    # Patch ProviderFactory and actual Providers
    from app.agents.provider.openai import OpenAIProvider
    
    original_execute = OpenAIProvider.execute_with_retry
    
    # Custom mock execute that matches agent type from prompt
    async def mock_execute(self, request, max_retries=2):
        # Determine agent type from system prompt
        for agent_type, response_data in mock_responses.items():
            if agent_type in request.system_prompt.lower():
                return create_mock_resp(response_data)
        # Default fallback
        return create_mock_resp({"message": "default mock"})

    OpenAIProvider.execute_with_retry = mock_execute

    try:
        workflow_id = str(uuid.uuid4())
        state = PipelineState(
            workflow_id=workflow_id,
            workspace_id="test-workspace",
            correlation_id=str(uuid.uuid4()),
            topic="Agentic AI",
            audience="CTOs",
            tone="professional",
            goals="Mock Test",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        
        final_state = await pipeline.execute(state, skip_human_review=True)
        
        print(f"Current Node: {final_state.current_node}")
        print(f"Node Results: {list(final_state.node_results.keys())}")
        
        # Validations
        if final_state.final_content and "Final Agentic AI Content" in final_state.final_content:
            print(f"[OK] Content reached Finalizer successfully")
        else:
            print(f"[FAIL] Final content mismatch: {final_state.final_content[:100]}")

        if final_state.research_data and "Deep research" in final_state.research_data.get("summary", ""):
            print("[OK] Research data integration verified")
            
        if final_state.all_nodes_completed():
             print("[OK] All 7 automated nodes completed successfully")
        else:
             print(f"[FAIL] Pipeline has errors: {final_state.errors}")

    except Exception as e:
        print(f"[CRITICAL] Mocked Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        OpenAIProvider.execute_with_retry = original_execute

if __name__ == "__main__":
    asyncio.run(test_end_to_end_pipeline_mocked())
