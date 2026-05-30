
import asyncio
import json
import uuid
import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_all_article_types_mocked():
    print("--- Starting End-to-End Content Type Validations (Mocked LLM) ---")
    
    from app.pipeline.graph import pipeline
    from app.pipeline.state import PipelineState
    from app.agents.provider.factory import provider_factory
    from app.agents.provider.base import ProviderResponse
    from app.agents.contracts import TokenUsage
    from app.agents.provider.openai import OpenAIProvider

    content_types = [
        {"topic": "Benefits of Remote Work", "type": "Blog article"},
        {"topic": "Best CRM Software 2026", "type": "Product comparison"},
        {"topic": "Quantum Computing 101", "type": "Technical article"},
        {"topic": "Climate Change Report 2026", "type": "Research summary"},
        {"topic": "Goose AI Release", "type": "News analysis"},
        {"topic": "Why AI Agents are the future", "type": "Social media thread"}
    ]

    # Helper to create successful ProviderResponse
    def create_mock_resp(content_dict):
        return ProviderResponse(
            success=True,
            content=json.dumps(content_dict),
            token_usage=TokenUsage(total_tokens=100, prompt_tokens=50, completion_tokens=50, provider="mock", model="mock"),
            latency_ms=5,
            provider="mock",
            model="mock"
        )

    original_execute = OpenAIProvider.execute_with_retry
    
    async def mock_execute(self, request, max_retries=2):
        # Very generic response generator to simulate success for any agent
        # We customize based on 'finalizer' to give a specific 'final_content' 
        # that includes the topic and type for verification
        
        sys_prompt = request.system_prompt.lower()
        
        if "research" in sys_prompt:
            return create_mock_resp({"summary": "Research summary", "key_points": ["Point 1"]})
        if "planner" in sys_prompt:
            return create_mock_resp({"title": "Plan Title", "sections": [{"title": "Intro"}]})
        if "writer" in sys_prompt:
            return create_mock_resp({"content": "# Draft content with enough length to pass checks. Lorem ipsum dolor sit amet.", "title": "Draft"})
        if "seo" in sys_prompt:
            return create_mock_resp({"primary_keywords": ["AI"], "content": "# SEO Optimized content"})
        if "fact_checker" in sys_prompt:
            return create_mock_resp({"verified_claims": ["C1"], "content": "# Fact Checked content"})
        if "compliance" in sys_prompt:
            return create_mock_resp({"compliance_status": "pass", "content": "# Compliant content"})
        if "finalizer" in sys_prompt:
            # We can't easily see the state here without more complex mocking, 
            # so we look at the user prompt which contains the topic
            user_prompt = request.messages[0]["content"]
            return create_mock_resp({
                "final_content": f"# Final Content for {user_prompt[:100]}\n\nValidated end-to-end.",
                "title": "Finalized Article",
                "word_count": 500
            })
            
        return create_mock_resp({"message": "fallback"})

    OpenAIProvider.execute_with_retry = mock_execute

    results = []
    try:
        for ct in content_types:
            print(f"Testing Content Type: {ct['type']} for topic: {ct['topic']}")
            state = PipelineState(
                workflow_id=str(uuid.uuid4()),
                workspace_id="test-ws",
                correlation_id=str(uuid.uuid4()),
                topic=ct['topic'],
                audience="general",
                tone="professional",
                goals=f"Generate a {ct['type']}",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            
            final_state = await pipeline.execute(state, skip_human_review=True)
            
            if final_state.all_nodes_completed() and final_state.final_content:
                print(f"[OK] {ct['type']} completed successfully")
                results.append(True)
            else:
                print(f"[FAIL] {ct['type']} failed or empty content. Errors: {final_state.errors}")
                results.append(False)

        if all(results):
            print("\n--- ALL CONTENT TYPES VALIDATED ---")
        else:
            print(f"\n--- VALIDATION FAILED for {results.count(False)} types ---")

    finally:
        OpenAIProvider.execute_with_retry = original_execute

if __name__ == "__main__":
    asyncio.run(test_all_article_types_mocked())
