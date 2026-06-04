from pydantic import BaseModel, Field


class FinalizerOutput(BaseModel):
    final_markdown: str = ""
    final_title: str = ""
    meta_title: str = ""
    meta_description: str = ""
    focus_keywords: list[str] = Field(default_factory=list)
    word_count: int = Field(default=0, ge=0)
    citations: list[dict] = Field(default_factory=list)
    overall_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    ready_for_publish: bool = False
