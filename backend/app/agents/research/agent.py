from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.research import ResearchInput
from app.schemas.agent_outputs.research import ResearchOutput
from app.schemas.research_packet import ResearchPacket, SourceSummary
from app.services.research_service import ResearchService
from app.log_config.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent(BaseAgent[ResearchInput, ResearchOutput]):
    def __init__(self):
        super().__init__()
        self._research_service = ResearchService()
        self._semaphore = asyncio.Semaphore(5)

    def system_prompt(self) -> str:
        return ""

    def parse_response(self, response: str, input_data: ResearchInput) -> ResearchOutput:
        return ResearchOutput()

    async def run(self, input_data: ResearchInput) -> ResearchOutput:
        queries = input_data.queries
        if not queries:
            logger.warning("No research queries provided")
            return ResearchOutput(
                research_packet=ResearchPacket.empty(),
                total_sources_found=0,
            )

        logger.info("Starting research", extra={"queries": len(queries)})

        async def search_task(query: str) -> list[dict]:
            async with self._semaphore:
                try:
                    return await self._research_service.search(query, max_results=input_data.max_sources_per_query)
                except Exception as e:
                    logger.warning("Search failed", extra={"query": query[:60], "error": str(e)[:100]})
                    return []

        coros = [search_task(q) for q in queries]
        all_results = await asyncio.gather(*coros, return_exceptions=True)

        all_sources: list[dict] = []
        for result in all_results:
            if isinstance(result, Exception):
                logger.warning("Research task exception", extra={"error": str(result)[:100]})
                continue
            all_sources.extend(result)

        packet = self._synthesize(all_sources, input_data.topic)

        logger.info("Research complete", extra={
            "sources": len(all_sources),
            "queries": len(queries),
            "findings": len(packet.key_findings),
        })

        return ResearchOutput(
            research_packet=packet,
            all_sources=all_sources,
            total_sources_found=len(all_sources),
        )

    def _synthesize(self, sources: list[dict], topic: str) -> ResearchPacket:
        domains = {}
        for src in sources:
            url = src.get("url", "")
            domain = url.split("/")[2] if "://" in url else "unknown"
            domains[domain] = domains.get(domain, 0) + 1

        top_domains = sorted(domains.items(), key=lambda x: -x[1])[:5]

        source_summaries = []
        for src in sources[:15]:
            url = src.get("url", "")
            domain = url.split("/")[2] if "://" in url else ""
            source_summaries.append(SourceSummary(
                url=url,
                domain=domain,
                title=src.get("title", ""),
                snippet=(src.get("content", "") or src.get("snippet", "") or "")[:300],
                trust_score=src.get("trust_score", 0.7),
            ))

        key_findings = []
        evidence_chunks = []
        for src in sources:
            snippet = src.get("snippet", "") or src.get("content", "") or ""
            if snippet and len(snippet) > 50:
                chunk = snippet[:250]
                if chunk not in key_findings:
                    key_findings.append(chunk)
                    evidence_chunks.append(snippet[:500])

        executive_summary = (
            f"Research gathered {len(sources)} sources from {len(domains)} unique domains "
            f"relevant to '{topic}'. "
        )
        if top_domains:
            executive_summary += f"Top sources from: {', '.join(d for d, _ in top_domains[:3])}."
        if key_findings:
            executive_summary += f" Extracted {len(key_findings)} key findings."

        return ResearchPacket(
            topic=topic,
            executive_summary=executive_summary,
            key_findings=key_findings[:25],
            statistics={
                "total_sources": len(sources),
                "unique_domains": len(domains),
                "top_domains": [{"domain": d, "count": c} for d, c in top_domains],
            },
            evidence_chunks=evidence_chunks[:50],
            source_summaries=source_summaries,
        )
