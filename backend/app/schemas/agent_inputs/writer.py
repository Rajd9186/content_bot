from pydantic import BaseModel, Field
from app.schemas.research_packet import ResearchPacket


class WriterInput(BaseModel):
    title: str
    topic: str = ""
    outline: dict = Field(default_factory=dict)
    research_packet: ResearchPacket = Field(default_factory=ResearchPacket.empty)
    verified_claims: list[dict] = Field(default_factory=list)
    tone: str = Field(default="professional")
    target_audience: str = Field(default="general")
    content_type: str = Field(default="article")
    seo_keywords: list[str] = Field(default_factory=list)
    rag_context: str = Field(default="")
