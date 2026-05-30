from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    WEB = "web"
    ACADEMIC = "academic"
    NEWS = "news"
    BLOG = "blog"
    DOCUMENTATION = "documentation"
    SOCIAL = "social"
    FORUM = "forum"


class SourceQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPAM = "spam"


class ResearchSource(BaseModel):
    id: Optional[str] = None
    url: str
    canonical_url: str
    domain: str
    title: str
    snippet: str
    content: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    published_date: Optional[datetime] = None
    source_type: SourceType = SourceType.WEB
    quality: SourceQuality = SourceQuality.MEDIUM
    
    # Scoring
    relevance_score: float = 0.0
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    recency_score: float = 0.0
    authority_score: float = 0.0
    trust_score: float = 0.0
    combined_score: float = 0.0
    
    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    embeddings: Optional[list[float]] = None
    content_hash: Optional[str] = None
    
    # Timestamps
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True


class ResearchQuery(BaseModel):
    query: str
    expanded_queries: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    domains: Optional[list[str]] = None
    exclude_domains: list[str] = Field(default_factory=list)
    max_results: int = 50
    time_range_days: Optional[int] = None
    source_types: list[SourceType] = Field(default_factory=lambda: [SourceType.WEB])
    min_quality: SourceQuality = SourceQuality.LOW


class ResearchResult(BaseModel):
    query: str
    sources: list[ResearchSource] = Field(default_factory=list)
    total_found: int = 0
    total_ingested: int = 0
    total_after_dedup: int = 0
    total_high_quality: int = 0
    search_latency_ms: float = 0.0
    ingestion_latency_ms: float = 0.0
    synthesis_latency_ms: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True


class SynthesizedFinding(BaseModel):
    finding: str = Field(min_length=20)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = Field(min_items=1)
    source_count: int = 0
    consensus_level: str = "high"
    contradiction_detected: bool = False
    statistical: bool = False
    expert_insight: bool = False
    trend: bool = False
    category: str = "general"
    
    def __init__(self, **data):
        super().__init__(**data)
        self.source_count = len(self.sources)


class ResearchSynthesis(BaseModel):
    topic: str
    summary: str = Field(default="")
    key_findings: list[SynthesizedFinding] = Field(default_factory=list)
    major_themes: list[str] = Field(default_factory=list)
    source_consensus: str = ""
    conflicting_viewpoints: list[str] = Field(default_factory=list)
    statistical_insights: list[str] = Field(default_factory=list)
    expert_commentary: list[str] = Field(default_factory=list)
    key_trends: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    
    top_sources: list[ResearchSource] = Field(default_factory=list)
    total_sources_analyzed: int = 0
    
    # For downstream agents
    writer_context: str = ""
    seo_keywords: list[str] = Field(default_factory=list)
    fact_check_claims: list[str] = Field(default_factory=list)
    
    @field_validator('summary', mode='after')
    @classmethod
    def ensure_summary_length(cls, v: str) -> str:
        if not v or len(v) < 50:
            return "Comprehensive research synthesis completed with analysis of multiple sources, identifying key findings, major themes, statistical insights, and expert perspectives for actionable content development."
        return v
    
    class Config:
        arbitrary_types_allowed = True


class Citation(BaseModel):
    source_id: str
    url: str
    title: str
    authors: list[str] = Field(default_factory=list)
    published_date: Optional[datetime] = None
    accessed_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    citation_format: str = "inline"
    citation_text: str = ""
    page_numbers: Optional[str] = None
    doi: Optional[str] = None
    
    def to_inline(self) -> str:
        if self.authors:
            author_str = self.authors[0] if len(self.authors) == 1 else f"{self.authors[0]} et al."
            year = self.published_date.year if self.published_date else "n.d."
            return f"[Source: {author_str}, {year}, {self.title[:50]}]"
        return f"[Source: {self.title[:50]}, {self.domain}]"
    
    @property
    def domain(self) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(self.url)
        return parsed.netloc.replace("www.", "")


class KnowledgePacket(BaseModel):
    """Structured research packet for downstream agents"""
    topic: str
    synthesis: ResearchSynthesis
    ranked_sources: list[ResearchSource]
    supporting_evidence: list[SynthesizedFinding]
    contradictions: list[str]
    statistics: list[str]
    expert_insights: list[str]
    trends: list[str]
    
    # Optimized for specific agents
    writer_brief: str = ""
    seo_data: dict[str, Any] = Field(default_factory=dict)
    validation_checklist: list[str] = Field(default_factory=list)
    fact_check_items: list[str] = Field(default_factory=list)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.writer_brief = self._build_writer_brief()
        self.seo_data = self._build_seo_data()
        self.validation_checklist = self._build_validation_checklist()
        self.fact_check_items = self._build_fact_check_items()
    
    def _build_writer_brief(self) -> str:
        parts = [f"Topic: {self.topic}"]
        if self.synthesis.summary:
            parts.append(f"\nOverview: {self.synthesis.summary}")
        if self.supporting_evidence:
            parts.append("\nKey Points to Cover:")
            for finding in self.supporting_evidence[:5]:
                parts.append(f"- {finding.finding}")
        return "\n".join(parts)
    
    def _build_seo_data(self) -> dict[str, Any]:
        keywords = list(set(self.synthesis.seo_keywords))
        return {
            "primary_keywords": keywords[:10],
            "secondary_keywords": keywords[10:20],
            "trending_topics": self.trends[:5],
            "expert_topics": [i.split(":")[0] for i in self.expert_insights[:5]],
        }
    
    def _build_validation_checklist(self) -> list[str]:
        checklist = []
        if self.contradictions:
            checklist.append(f"Address {len(self.contradictions)} contradictory viewpoints")
        if self.statistics:
            checklist.append(f"Include {len(self.statistics)} statistical findings")
        if self.expert_insights:
            checklist.append(f"Reference {len(self.expert_insights)} expert insights")
        return checklist
    
    def _build_fact_check_items(self) -> list[str]:
        items = []
        for finding in self.supporting_evidence:
            if finding.statistical or finding.confidence > 0.8:
                items.append(finding.finding)
        return items


@dataclass
class ResearchContext:
    correlation_id: str
    workflow_id: Optional[str] = None
    workspace_id: Optional[str] = None
    content_item_id: Optional[str] = None
    query: Optional[ResearchQuery] = None
    result: Optional[ResearchResult] = None
    synthesis: Optional[ResearchSynthesis] = None
    packet: Optional[KnowledgePacket] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None