from pydantic import BaseModel, Field


class FactCheckerInput(BaseModel):
    markdown: str
    citations: list[dict] = Field(default_factory=list)
    verified_claims: list[dict] = Field(default_factory=list)
    research_packet: dict = Field(default_factory=dict)
