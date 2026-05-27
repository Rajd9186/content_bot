from pydantic import BaseModel, Field


class SEOOutput(BaseModel):
    meta_title: str = Field(default="")
    meta_description: str = Field(default="")
    focus_keywords: list[str] = Field(default_factory=list)
    seo_score: float = Field(default=0.0, ge=0.0, le=1.0)
    suggestions: list[str] = Field(default_factory=list)
    optimized_markdown: str = Field(default="")
