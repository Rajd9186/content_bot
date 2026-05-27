from pydantic import BaseModel, Field


class OutlineInput(BaseModel):
    topic: str
    research_packet: dict = Field(default_factory=dict)
    planner_outline: dict = Field(default_factory=dict)
    content_type: str = Field(default="article")
