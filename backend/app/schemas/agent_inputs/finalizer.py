from pydantic import BaseModel, Field


class FinalizerInput(BaseModel):
    markdown: str
    title: str = ""
    meta_title: str = ""
    meta_description: str = ""
    focus_keywords: list[str] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    seo_score: float = Field(default=0.0, ge=0.0, le=1.0)
    fact_check_passed: bool = True
