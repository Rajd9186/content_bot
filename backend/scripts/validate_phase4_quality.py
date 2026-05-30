import asyncio
import json
import uuid
import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_agent_runtime_and_quality():
    print("--- PHASE 4: AGENT RUNTIME & CONTENT QUALITY VALIDATION ---")
    
    from app.pipeline.graph import pipeline
    from app.pipeline.state import PipelineState
    from app.agents.provider.openai import OpenAIProvider
    from app.agents.contracts import TokenUsage
    from app.agents.provider.base import ProviderResponse

    # 1. Validation of "Research Summary" Quality & Prompt Construction
    # We verify that the builders actually create structured prompts
    from app.pipeline.prompts import build_user_prompt
    
    mock_state = {
        "topic": "Agentic AI",
        "research_data": {
            "summary": "This is a meaningful synthesis of findings.",
            "key_points": ["Insight 1", "Insight 2"],
            "statistics": ["99% efficiency"]
        }
    }
    
    writer_prompt = build_user_prompt("writer", mock_state)
    
    prompt_checks = []
    if "Research Context" in writer_prompt and "Key Findings" in writer_prompt:
        prompt_checks.append("[OK] Prompt contains Research Context and Findings.")
    else:
        prompt_checks.append("[FAIL] Prompt missing structured research context.")
        
    if "### Outline to Follow" in writer_prompt:
        prompt_checks.append("[OK] Prompt contains Outline instructions.")
    else:
        prompt_checks.append("[FAIL] Prompt missing outline.")

    # 2. End-to-End Generation & Quality Check (Mocked Providers)
    mock_responses = {
        "research": {
            "summary": "Comprehensive analysis of agentic workflows.",
            "key_points": ["Autonomous decision making", "Tool use"],
            "statistics": ["30% faster than LLM alone"],
            "citations": ["Source A: Principles of Agents"],
            "entities": ["Goose", "Enterprise"],
            "risks": ["Safety"],
            "outline_suggestions": ["Intro", "Workflows", "Safety"],
            "gaps": ["None"],
            "contradictions": ["None"]
        },
        "planner": {
            "title": "The Power of Agentic AI",
            "sections": [{"title": "Introduction", "key_points": ["Define Agents"]}],
            "goals": ["Educate"],
            "target_audience": ["General"],
            "key_themes": ["AI"],
            "research_questions": ["What?"],
            "success_criteria": ["Clarity"],
            "estimated_word_count": 800
        },
        "writer": {
            "content": "# The Power of Agentic AI\n\nAgentic AI represents a shift from passive models to active assistants. [Source A]. Statistics show 30% speed increases.",
            "title": "The Power of Agentic AI",
            "word_count": 800,
            "sections_written": ["Intro"],
            "citations_used": ["Source A"]
        },
        "seo": {
            "primary_keywords": ["AI"],
            "content": "# Optimized Agentic AI Content"
        },
        "fact_checker": {
            "verified_claims": ["C1"],
            "content": "# Fact-Checked Content"
        },
        "compliance": {
            "compliance_status": "pass",
            "content": "# Compliant Content"
        },
        "finalizer": {
            "final_content": "# FINAL ARTICLE: Agentic AI\n\nFull publication ready text.",
            "title": "Finalized Article",
            "word_count": 800
        }
    }

    def create_mock_resp(content_dict):
        return ProviderResponse(
            success=True,
            content=json.dumps(content_dict),
            token_usage=TokenUsage(total_tokens=100, prompt_tokens=50, completion_tokens=50, provider="mock", model="mock"),
            latency_ms=10,
            provider="mock",
            model="mock"
        )

    original_execute = OpenAIProvider.execute_with_retry
    
    async def mock_execute(self, request, max_retries=2):
        for agent_type, response_data in mock_responses.items():
            if agent_type in request.system_prompt.lower():
                return create_mock_resp(response_data)
        return create_mock_resp({"message": "default"})

    OpenAIProvider.execute_with_retry = mock_execute

    quality_results = []
    try:
        state = PipelineState(
            workflow_id=str(uuid.uuid4()),
            workspace_id="test",
            topic="Agentic AI",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        
        final_state = await pipeline.execute(state, skip_human_review=True)
        
        # 3. Content Quality Validation
        if final_state.final_content and "# FINAL ARTICLE" in final_state.final_content:
            quality_results.append("[OK] Final content correctly assembled.")
        else:
            quality_results.append("[FAIL] Final content empty or malformed.")
            
        if final_state.research_data and "agentic workflows" in final_state.research_data.get("summary", ""):
             quality_results.append("[OK] Research summary is meaningful synthesis.")
        else:
             quality_results.append("[FAIL] Research summary is weak/placeholder.")

        # Check for "Untitled" rejection
        if "Untitled" in final_state.final_content[:50]:
            quality_results.append("[FAIL] Content generated with 'Untitled' title.")
        else:
            quality_results.append("[OK] Content title is preserved correctly.")

    finally:
        OpenAIProvider.execute_with_retry = original_execute

    report = {
        "phase": "PHASE 4 — CONTENT QUALITY",
        "prompt_validation": prompt_checks,
        "generation_quality": quality_results,
        "status": "PASS" if all("OK" in r for r in prompt_checks + quality_results) else "FAIL"
    }
    
    print(json.dumps(report, indent=2))
    with open("phase4_quality_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    asyncio.run(test_agent_runtime_and_quality())
