from pydantic import BaseModel, Field


class WriterOutput(BaseModel):
    markdown: str = Field(default="")
    summary: str = Field(default="")
    word_count: int = Field(default=0, ge=0)
    citations: list[dict] = Field(default_factory=list)
    headings_used: list[str] = Field(default_factory=list)
    seo_metadata: dict = Field(default_factory=dict)
    is_valid: bool = Field(default=False)
    validation_errors: list[str] = Field(default_factory=list)
    generation_attempts: int = Field(default=1, ge=1)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
