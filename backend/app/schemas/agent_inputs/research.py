from pydantic import BaseModel, Field


class ResearchInput(BaseModel):
    topic: str
    queries: list[str] = Field(default_factory=list)
    max_sources_per_query: int = Field(default=5, ge=1, le=20)
    existing_sources: list[dict] = Field(default_factory=list)
