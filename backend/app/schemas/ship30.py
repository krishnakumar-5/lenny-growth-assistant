from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.chat import SourceCitation


class Ship30Request(BaseModel):
    """Request payload for generating a Ship 30 for 30 Atomic Essay."""
    topic: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="The growth, product, or retention topic to write about.",
        json_schema_extra={"example": "The 14-day reverse trial in product-led growth"},
    )
    target_audience: Optional[str] = Field(
        default="Product Managers, Growth Leaders, and Founders",
        description="The primary target reader for the essay.",
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider ('ollama' or 'anthropic').",
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model name.",
    )


class Ship30Response(BaseModel):
    """Response containing the generated grounded growth essay artifact."""
    title: str = Field(..., description="High-impact, scroll-stopping headline.")
    hook: str = Field(..., description="First 1-2 sentence hook.")
    word_count: int = Field(..., description="Total word count of the essay body.")
    within_constraints: bool = Field(
        ...,
        description="True if word count adheres to the 1,150-1,350 word target range (~1,250 words).",
    )
    content_markdown: str = Field(..., description="Full essay in formatted Markdown.")
    content_html: str = Field(..., description="Sanitized, self-contained HTML card for preview.")
    guest_attribution: str = Field(..., description="Podcast guest credited for the core framework.")
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="Source citations from verified podcast transcripts.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Generation timestamp in UTC.",
    )
