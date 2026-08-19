from pydantic import BaseModel, Field, field_validator


class SectionBreakdownSchema(BaseModel):
    heading: str = Field(
        ..., description="Section title or main topic heading identified in document"
    )
    summary: str = Field(
        ..., description="Brief summary of content covered under this section"
    )


class EntityDetectionSchema(BaseModel):
    organizations: list[str] = Field(
        default_factory=list, description="Organization or company names mentioned"
    )
    dates: list[str] = Field(
        default_factory=list, description="Important dates, deadlines, or time periods mentioned"
    )
    locations: list[str] = Field(
        default_factory=list, description="Locations, addresses, cities, or countries mentioned"
    )
    people: list[str] = Field(
        default_factory=list, description="Person names or key stakeholders mentioned"
    )
    monetary_amounts: list[str] = Field(
        default_factory=list, description="Monetary amounts, prices, or financial values mentioned"
    )
    emails_and_contacts: list[str] = Field(
        default_factory=list, description="Email addresses, phone numbers, or contact info mentioned"
    )


class DocumentMetricsSchema(BaseModel):
    reading_time_minutes: float = Field(
        default=1.0, ge=0.0, description="Estimated reading time in minutes"
    )
    key_technologies_mentioned: list[str] = Field(
        default_factory=list, description="Technologies, tools, or domain-specific tools identified"
    )
    urgency_level: str = Field(
        default="Informational",
        description="Assessed urgency or priority (e.g., Critical, High, Normal, Informational)",
    )


class DocumentAnalysisSchema(BaseModel):
    """
    Comprehensive Pydantic schema enforcing detailed, multi-dimensional JSON analysis
    for any document type (Resume, Invoice, Contract, Report, Technical Paper, etc.).
    """

    title: str = Field(
        ..., description="Concise, highly descriptive title for the document"
    )
    summary: str = Field(
        ..., description="Clear executive summary summarizing the core contents of the document"
    )
    document_category: str = Field(
        default="General Document",
        description="Document type (e.g., Resume / CV, Invoice, Legal Contract, Technical Specification, Medical Report, Financial Statement)",
    )
    confidence_score: float = Field(
        default=0.98,
        ge=0.0,
        le=1.0,
        description="AI extraction confidence score (0.0 to 1.0)",
    )
    sentiment_tone: str = Field(
        default="Professional & Objective",
        description="Overall tone and style (e.g. Professional, Formal, Urgent, Technical)",
    )
    readability_level: str = Field(
        default="Intermediate",
        description="Target readability level (e.g. Basic, Intermediate, Advanced / Technical, Executive)",
    )
    executive_takeaway: str = Field(
        default="",
        description="Single sentence core bottom-line takeaway of the document",
    )
    keywords: list[str] = Field(
        ..., min_length=1, description="List of 5 to 15 key topics or keywords"
    )
    key_insights: list[str] = Field(
        default_factory=list, description="Detailed bullet points of key takeaways and findings"
    )
    section_breakdown: list[SectionBreakdownSchema] = Field(
        default_factory=list, description="Major sections/headings found in document with brief summaries"
    )
    action_items: list[str] = Field(
        default_factory=list, description="Action items, recommendations, or next steps identified"
    )
    entities: EntityDetectionSchema = Field(
        default_factory=EntityDetectionSchema,
        description="Extracted entities categorized by type",
    )
    metadata_metrics: DocumentMetricsSchema = Field(
        default_factory=DocumentMetricsSchema,
        description="Document metrics including reading time, technologies, and urgency level",
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
