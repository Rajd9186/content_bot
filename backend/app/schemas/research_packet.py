from pydantic import BaseModel, Field
from typing import Any


class SourceSummary(BaseModel):
    url: str = ""
    domain: str = ""
    title: str = ""
    snippet: str = ""
    trust_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ResearchPacket(BaseModel):
    topic: str = ""
    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
    controversies: list[str] = Field(default_factory=list)
    evidence_chunks: list[str] = Field(default_factory=list)
    source_summaries: list[SourceSummary] = Field(default_factory=list)
    outline_suggestions: list[str] = Field(default_factory=list)
    citation_map: dict[str, list[str]] = Field(default_factory=dict)

    @classmethod
    def empty(cls) -> "ResearchPacket":
        return cls(
            executive_summary="No research sources available.",
            statistics={"total_sources": 0, "unique_domains": 0},
        )


class DraftValidationResult(BaseModel):
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    hallucination_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
