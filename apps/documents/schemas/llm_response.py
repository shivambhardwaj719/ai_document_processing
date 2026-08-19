from pydantic import BaseModel, Field, field_validator


class DocumentAnalysisSchema(BaseModel):
    """
    Pydantic schema enforcing structured JSON output for document analysis.
    """

    title: str = Field(
        ..., description="Concise, descriptive title for the document based on content"
    )
    summary: str = Field(..., description="Clear summary summarizing key points of the document")
    keywords: list[str] = Field(
        ..., min_length=1, description="List of 3 to 10 key topics or keywords"
    )
    language: str = Field(
        ..., description="Primary language of the document (e.g., English, Spanish)"
    )
    word_count: int = Field(..., ge=0, description="Total word count of extracted document text")

    @field_validator("title", "summary", "language")
    @classmethod
    def check_non_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace.")
        return v.strip()

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, v: list[str]) -> list[str]:
        cleaned = [k.strip() for k in v if k and k.strip()]
        if not cleaned:
            raise ValueError("Keywords list must contain at least one non-empty string.")
        return cleaned
