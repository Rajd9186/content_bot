from __future__ import annotations

import logging
from typing import Any, Optional

from app.research.models import (
    KnowledgePacket, ResearchSource, ResearchSynthesis, SynthesizedFinding,
)

logger = logging.getLogger(__name__)


class KnowledgePackager:
    """
    Creates structured research packets optimized for downstream agents.
    """
    
    def package(
        self,
        synthesis: ResearchSynthesis,
        sources: list[ResearchSource],
        topic: str,
    ) -> KnowledgePacket:
        logger.info("Creating knowledge packet for: %s", topic)
        
        supporting_evidence = [
            f for f in synthesis.key_findings
            if f.confidence > 0.6 and f.source_count >= 1
        ]
        
        statistics = synthesis.statistical_insights or [
            f.finding for f in synthesis.key_findings if f.statistical
        ]
        
        expert_insights = synthesis.expert_commentary or [
            f.finding for f in synthesis.key_findings if f.expert_insight
        ]
        
        packet = KnowledgePacket(
            topic=topic,
            synthesis=synthesis,
            ranked_sources=sources[:15],
            supporting_evidence=supporting_evidence[:10],
            contradictions=synthesis.contradictions,
            statistics=statistics[:5],
            expert_insights=expert_insights[:5],
            trends=synthesis.key_trends,
        )
        
        logger.info(
            "Knowledge packet created: %d sources, %d findings, %d statistics",
            len(packet.ranked_sources),
            len(packet.supporting_evidence),
            len(packet.statistics)
        )
        
        return packet

    def for_writer(self, packet: KnowledgePacket) -> str:
        sections = [
            f"# Research Brief: {packet.topic}",
            "",
            "## Overview",
            packet.synthesis.summary,
            "",
            "## Key Points to Cover",
        ]
        
        for i, finding in enumerate(packet.supporting_evidence[:5], 1):
            sections.append(f"{i}. {finding.finding}")
            if finding.sources:
                sections.append(f"   Sources: {len(finding.sources)}")
        
        if packet.contradictions:
            sections.append("")
            sections.append("## Contradictions to Address")
            for contradiction in packet.contradictions:
                sections.append(f"- {contradiction}")
        
        if packet.statistics:
            sections.append("")
            sections.append("## Statistics to Include")
            for stat in packet.statistics:
                sections.append(f"- {stat[:100]}")
        
        if packet.expert_insights:
            sections.append("")
            sections.append("## Expert Perspectives")
            for insight in packet.expert_insights:
                sections.append(f"- {insight[:100]}")
        
        sections.append("")
        sections.append("## Top Sources")
        for source in packet.ranked_sources[:5]:
            sections.append(f"- {source.title} ({source.domain})")
        
        return "\n".join(sections)

    def for_seo(self, packet: KnowledgePacket) -> dict[str, Any]:
        return {
            "primary_keywords": packet.synthesis.seo_keywords[:10],
            "secondary_keywords": packet.synthesis.seo_keywords[10:20],
            "trending_topics": packet.trends[:5],
            "expert_topics": [i.split(":")[0] for i in packet.expert_insights[:5]],
            "content_angles": [
                f.finding[:80] for f in packet.supporting_evidence[:5]
            ],
            "unique_selling_points": [
                stat[:100] for stat in packet.statistics[:3]
            ],
        }

    def for_validator(self, packet: KnowledgePacket) -> list[str]:
        checklist = [
            f"Cover topic: {packet.topic}",
            f"Include {len(packet.supporting_evidence)} key findings",
        ]
        
        if packet.contradictions:
            checklist.append(f"Address {len(packet.contradictions)} contradictory viewpoints")
        
        if packet.statistics:
            checklist.append(f"Include {len(packet.statistics)} statistical findings")
        
        if packet.expert_insights:
            checklist.append(f"Reference {len(packet.expert_insights)} expert insights")
        
        checklist.append(f"Use {len(packet.ranked_sources)} ranked sources for citations")
        
        if packet.synthesis.gaps:
            checklist.append(f"Acknowledge gaps: {', '.join(packet.synthesis.gaps[:3])}")
        
        return checklist

    def for_fact_checker(self, packet: KnowledgePacket) -> list[dict[str, Any]]:
        items = []
        
        for finding in packet.supporting_evidence:
            if finding.statistical or finding.confidence > 0.8:
                items.append({
                    "claim": finding.finding,
                    "confidence": finding.confidence,
                    "sources": finding.sources,
                    "source_count": finding.source_count,
                    "needs_verification": finding.statistical,
                    "category": finding.category,
                })
        
        for stat in packet.statistics:
            items.append({
                "claim": stat,
                "confidence": 0.9,
                "sources": [],
                "source_count": 1,
                "needs_verification": True,
                "category": "statistical",
            })
        
        return items


knowledge_packager = KnowledgePackager()