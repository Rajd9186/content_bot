from pydantic import BaseModel, Field


class ValidatorOutput(BaseModel):
    is_valid: bool = Field(default=False)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    word_count: int = Field(default=0)
    citation_count: int = Field(default=0)
    missing_sections: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    hallucination_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
