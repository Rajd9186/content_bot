from pydantic import BaseModel, Field


class SEOInput(BaseModel):
    markdown: str
    title: str
    seo_keywords: list[str] = Field(default_factory=list)
    content_type: str = Field(default="article")
