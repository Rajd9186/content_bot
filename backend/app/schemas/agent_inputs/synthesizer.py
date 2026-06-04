from pydantic import BaseModel, Field
from app.schemas.research_packet import ResearchPacket


class SynthesizerInput(BaseModel):
    topic: str
    research_packet: ResearchPacket = Field(default_factory=ResearchPacket.empty)
    planner_outline: dict = Field(default_factory=dict)
    target_keywords: list[str] = Field(default_factory=list)
