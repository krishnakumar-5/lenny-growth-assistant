from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.schemas.sources import SearchResultItem
from app.services.retrieval import search_transcripts

RETRIEVAL_TOOL_NAME = "search_podcast_transcripts"

RETRIEVAL_TOOL_SPEC: Dict[str, Any] = {
    "name": RETRIEVAL_TOOL_NAME,
    "description": (
        "Search the knowledge base of Lenny's Podcast transcripts for relevant discussions, "
        "frameworks, growth tactics, benchmarks, and guest advice using keywords and topic phrases."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords, guest names, or topics to query in the transcripts.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of relevant chunks to retrieve (1-10). Default is 4.",
                "default": 4,
            },
        },
        "required": ["query"],
    },
}


def execute_retrieval_tool(
    db: Session,
    query: str,
    limit: int = 4,
) -> List[SearchResultItem]:
    """Execute the transcript retrieval tool against the database knowledge base."""
    return search_transcripts(db=db, query=query, limit=limit)
