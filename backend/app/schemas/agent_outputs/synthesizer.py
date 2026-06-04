from pydantic import BaseModel, Field


class SynthesizerOutput(BaseModel):
    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)
    synthesized_outline: dict = Field(default_factory=dict)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
