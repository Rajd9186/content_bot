from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    outline: dict = Field(default_factory=dict)
    sections: list[dict] = Field(default_factory=list)
    research_tasks: list[str] = Field(default_factory=list)
    target_keywords: list[str] = Field(default_factory=list)
    suggested_sources: list[str] = Field(default_factory=list)
