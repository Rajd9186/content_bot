from __future__ import annotations

import logging
from typing import Any

from app.agents.contracts import AgentInput
from app.research import (
    citation_engine,
    knowledge_packager,
    research_pipeline,
    research_synthesis,
)
from app.research.models import ResearchQuery, SourceQuality
from app.research.providers.mock import MockSearchProvider

logger = logging.getLogger(__name__)


class ResearchAgentIntegration:
    """
    Integrates Phase 5 Research Intelligence with Phase 4 Agent Runtime.

    Provides research-backed context for all downstream agents:
    - Researcher Agent: Full research pipeline execution
    - Writer Agent: Research-backed content generation
    - SEO Agent: Keyword extraction from research
    - Validator Agent: Source validation checklist
    - Fact Checker: Claim extraction and verification
    """

    def __init__(self) -> None:
        self._initialized = False
        self._mock_provider_registered = False

    async def initialize(self) -> None:
        """Initialize research pipeline with available providers"""
        if self._initialized:
            return

        # Register mock provider for testing (remove in production)
        if not self._mock_provider_registered:
            import os

            from app.research.providers.factory import search_provider_factory

            # Only use mock if no real API keys configured
            if not os.getenv("TAVILY_API_KEY") and not os.getenv("SERPER_API_KEY"):
                search_provider_factory.register(MockSearchProvider())
                self._mock_provider_registered = True
                logger.info("Mock search provider registered (no API keys configured)")

        self._initialized = True
        logger.info("Research integration initialized")

    async def execute_research(
        self,
        topic: str,
        query: str,
        correlation_id: str,
        workflow_id: str | None = None,
        max_results: int = 50,
        time_range_days: int | None = 90,
        topics: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute complete research pipeline and return knowledge packet.

        Args:
            topic: Main research topic
            query: Search query
            correlation_id: Workflow correlation ID
            workflow_id: Optional workflow ID
            max_results: Maximum sources to return
            time_range_days: Filter by recency
            topics: Sub-topics for expanded search

        Returns:
            Knowledge packet with research findings, sources, and agent-ready data
        """
        await self.initialize()

        # Build research query
        research_query = ResearchQuery(
            query=query,
            topics=topics or [],
            max_results=max_results,
            time_range_days=time_range_days,
            source_types=["web", "news", "academic", "blog"],
            min_quality=SourceQuality.LOW,
        )

        # Execute pipeline
        logger.info("Executing research pipeline for: %s", query)
        result = await research_pipeline.execute(
            query=research_query,
            correlation_id=correlation_id,
        )

        logger.info(
            "Research complete: %d sources found, %d after dedup, %d high quality",
            result.total_found,
            result.total_after_dedup,
            result.total_high_quality,
        )

        # Synthesize findings
        logger.info("Synthesizing research findings")
        synthesis = await research_synthesis.synthesize(
            sources=result.sources,
            topic=topic,
            query=query,
        )

        # Generate citations
        logger.info("Generating citations for %d sources", len(result.sources))
        citations = citation_engine.generate_citations(result.sources)

        # Package knowledge for agents
        logger.info("Creating knowledge packet")
        packet = knowledge_packager.package(
            synthesis=synthesis,
            sources=result.sources,
            topic=topic,
        )

        return {
            "success": True,
            "topic": topic,
            "query": query,
            "correlation_id": correlation_id,
            "workflow_id": workflow_id,
            "sources_found": result.total_found,
            "sources_after_dedup": result.total_after_dedup,
            "high_quality_sources": result.total_high_quality,
            "key_findings_count": len(synthesis.key_findings),
            "themes_count": len(synthesis.major_themes),
            "statistics_count": len(synthesis.statistical_insights),
            "expert_insights_count": len(synthesis.expert_commentary),
            "contradictions_count": len(synthesis.contradictions),
            "citations_generated": len(citations),
            "packet": packet,
            "synthesis": synthesis,
            "sources": result.sources,
            "writer_brief": packet.writer_brief,
            "seo_data": packet.seo_data,
            "validation_checklist": packet.validation_checklist,
            "fact_check_items": packet.fact_check_items,
        }

    async def get_research_context(
        self,
        agent_input: AgentInput,
        topic_field: str = "topic",
        query_field: str = "query",
    ) -> dict[str, Any]:
        """
        Extract research parameters from agent input and execute research.

        Args:
            agent_input: Phase 4 agent input
            topic_field: Field name for topic in template_kwargs
            query_field: Field name for search query

        Returns:
            Research context dictionary
        """
        kwargs = agent_input.metadata.get("template_kwargs", {})

        topic = kwargs.get(topic_field, kwargs.get("title", "Research Topic"))
        query = kwargs.get(query_field, topic)
        topics = kwargs.get("topics", kwargs.get("subtopics", []))

        return await self.execute_research(
            topic=topic,
            query=query,
            correlation_id=agent_input.correlation_id,
            workflow_id=agent_input.workflow_id,
            topics=topics if isinstance(topics, list) else [],
        )


# Singleton instance
research_integration = ResearchAgentIntegration()
