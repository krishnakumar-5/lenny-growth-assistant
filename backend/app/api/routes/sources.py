from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sources import SourceSearchRequest, SourceSearchResponse
from app.services.retrieval import search_transcripts

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post(
    "/search",
    response_model=SourceSearchResponse,
    summary="Search Transcript Sources",
    description="Retrieve relevant podcast transcript chunks matching query keywords with source provenance.",
)
def search_sources(
    payload: SourceSearchRequest,
    db: Session = Depends(get_db),
) -> SourceSearchResponse:
    """Search ingested transcript chunks and return ranked results."""
    results = search_transcripts(
        db=db,
        query=payload.query,
        limit=payload.limit,
    )

    return SourceSearchResponse(
        query=payload.query,
        total_results=len(results),
        results=results,
    )
