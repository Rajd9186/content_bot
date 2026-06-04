from pydantic import BaseModel, Field


class PlannerInput(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    title: str = Field(default="", max_length=500)
    content_type: str = Field(default="article")
    tone: str = Field(default="professional")
    target_audience: str = Field(default="general")
    points_to_cover: list[str] = Field(default_factory=list)
    seo_keywords: list[str] = Field(default_factory=list)
