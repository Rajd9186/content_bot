from __future__ import annotations

import logging
from typing import Any

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, NodeStatus, PipelineState
from app.services.source_governance import SourceGovernanceEngine
from app.infrastructure.database import async_session_factory

logger = logging.getLogger(__name__)


class ResearchAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("research")

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        # 1. Apply Source Governance to the system prompt
        project_id = state.metadata.get("project_id")
        if project_id:
            async with async_session_factory() as session:
                gov_engine = SourceGovernanceEngine(session)
                policy = await gov_engine._repo.get_source_policy(project_id)
                if policy and policy.enabled:
                    allowed = await gov_engine._repo.get_allowed_sources(project_id)
                    blocked = await gov_engine._repo.get_blocked_sources(project_id)
                    
                    gov_text = "\nSOURCE GOVERNANCE POLICIES:\n"
                    if allowed:
                        gov_text += f"- Prioritize these sources: {', '.join([s.source_name for s in allowed])}\n"
                    if blocked:
                        gov_text += f"- STRICTLY FORBIDDEN sources: {', '.join([s.source_name for s in blocked])}\n"
                    
                    # Inject into the agent's internal provider request via a custom system prompt extension
                    # Since super().execute() builds the prompt internally, we have to be careful.
                    # We can temporarily modify the build_system_prompt behavior or pass it as part of state.
                    # For now, let's rely on the fact that super().execute() uses build_system_prompt(self.agent_type).
                    # To properly inject, we should update build_system_prompt or pass additional context.
                    # However, a simpler way is to add it to the user prompt via state.
                    state.metadata["source_governance"] = gov_text

        result = await super().execute(state, provider_override, model_override)
        
        if result.status == NodeStatus.SUCCESS:
            vlog_links = result.output.get("vlog_links", [])
            if isinstance(vlog_links, list):
                # 2. Post-process and filter research sources
                if project_id:
                    async with async_session_factory() as session:
                        gov_engine = SourceGovernanceEngine(session)
                        # Convert vlog_links (likely strings or dicts) to a format the engine expects
                        sources = []
                        for link in vlog_links:
                            if isinstance(link, str):
                                sources.append({"name": "Unknown", "domain": link, "trust_score": 50})
                            elif isinstance(link, dict):
                                sources.append({
                                    "name": link.get("name", "Unknown"),
                                    "domain": link.get("domain", ""),
                                    "trust_score": link.get("trust_score", 50),
                                    "published_at": link.get("published_at")
                                })
                        
                        filtered_sources, report = await gov_engine.apply_governance(project_id, sources)
                        
                        # Map back to vlog_links format
                        vlog_links = [
                            s if isinstance(s, dict) else s 
                            for s in filtered_sources
                        ]
                        state.metadata["source_governance_report"] = report
                
                state.vlog_links = vlog_links
        return result

def extract_research_data(output: dict[str, Any]) -> dict[str, Any]:


def extract_research_data(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": output.get("summary", "Research completed."),
        "key_points": output.get("key_points", []),
        "statistics": output.get("statistics", []),
        "citations": output.get("citations", []),
        "entities": output.get("entities", []),
        "risks": output.get("risks", []),
        "outline_suggestions": output.get("outline_suggestions", []),
        "gaps": output.get("gaps", []),
        "contradictions": output.get("contradictions", []),
    }
