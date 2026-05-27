from pydantic import BaseModel, Field
from app.schemas.research_packet import ResearchPacket


class ResearchOutput(BaseModel):
    research_packet: ResearchPacket
    all_sources: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    total_sources_found: int = 0
