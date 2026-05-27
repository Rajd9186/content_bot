from pydantic import BaseModel, Field


class OutlineOutput(BaseModel):
    sections: list[dict] = Field(default_factory=list)
    target_keywords: list[str] = Field(default_factory=list)
    suggested_structure: str = Field(default="")
