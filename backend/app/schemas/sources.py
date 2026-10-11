from typing import Any, Dict, List
import uuid
from pydantic import BaseModel, Field, field_validator


class SourceSearchRequest(BaseModel):
    """Payload for knowledge base retrieval search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query string or keywords",
        examples=["retention metrics"],
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of relevant chunks to retrieve (1-50)",
        examples=[5],
    )
    include_synthetic: bool = Field(
        default=False,
        description="Whether to include synthetic test fixtures in retrieval results",
    )

    @field_validator("query")
    @classmethod
    def validate_non_empty_query(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Query string cannot be empty or pure whitespace.")
        return clean


class SearchResultItem(BaseModel):
    """An individual retrieved transcript chunk with provenance details."""

    chunk_id: uuid.UUID = Field(..., description="Unique chunk UUID")
    transcript_id: uuid.UUID = Field(..., description="Unique parent transcript UUID")
    transcript_title: str = Field(..., description="Title of the source transcript")
    source_filename: str = Field(..., description="Disk filename of the source transcript")
    chunk_index: int = Field(..., description="Chunk sequence index within the transcript")
    chunk_text: str = Field(..., description="Text content of the retrieved chunk")
    score: float = Field(..., description="Calculated keyword match score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance and location metadata",
    )


class SourceSearchResponse(BaseModel):
    """Structured response containing query and retrieved transcript results."""

    query: str = Field(..., description="Echoed input query")
    total_results: int = Field(..., description="Number of retrieved chunks")
    results: List[SearchResultItem] = Field(
        default_factory=list,
        description="Ranked list of relevant transcript chunks",
    )
