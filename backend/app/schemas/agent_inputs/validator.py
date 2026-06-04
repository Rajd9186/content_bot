from pydantic import BaseModel, Field


class ValidatorInput(BaseModel):
    markdown: str
    title: str = ""
    citations: list[dict] = Field(default_factory=list)
    min_word_count: int = Field(default=300, ge=50)
    required_sections: list[str] = Field(default_factory=list)
