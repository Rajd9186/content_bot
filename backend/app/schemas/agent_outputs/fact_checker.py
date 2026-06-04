from pydantic import BaseModel, Field


class FactCheckerOutput(BaseModel):
    is_pass: bool = Field(default=False)
    errors: list[dict] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)
    corrected_citations: list[dict] = Field(default_factory=list)
    hallucination_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    corrected_markdown: str = Field(default="")
