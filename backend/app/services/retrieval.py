import re
from typing import List, Optional, Set
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.transcript import Transcript, TranscriptChunk
from app.schemas.sources import SearchResultItem

TEST_FIXTURE_SOURCE_IDS: Set[str] = {
    "sample_growth_accounting",
    "elena_verna_plg",
    "brian_balfour_loops",
    "shreyas_doshi_strategy",
    "synthetic_growth_benchmark",
}

def is_synthetic_or_fixture(transcript: Transcript, chunk: Optional[TranscriptChunk] = None) -> bool:
    """Determine whether a transcript or chunk is a synthetic benchmark or test fixture.

    Checks explicit flags in metadata, recognized fixture source IDs, and title tags.
    """
    # 1. Explicit metadata flags on transcript
    t_meta = transcript.meta_info if isinstance(transcript.meta_info, dict) else {}
    if t_meta.get("synthetic_test_data") in (True, "true", "True", "synthetic_test_data"):
        return True
    if t_meta.get("is_test_fixture") in (True, "true", "True"):
        return True
    if t_meta.get("data_classification") in ("synthetic_test_data", "test_fixture"):
        return True

    # 2. Explicit metadata flags on chunk
    if chunk is not None:
        c_meta = chunk.meta_info if isinstance(chunk.meta_info, dict) else {}
        if c_meta.get("synthetic_test_data") in (True, "true", "True", "synthetic_test_data"):
            return True
        if c_meta.get("is_test_fixture") in (True, "true", "True"):
            return True
        if c_meta.get("data_classification") in ("synthetic_test_data", "test_fixture"):
            return True

    # 3. Explicit title markers
    title_lower = (transcript.title or "").lower()
    if "[synthetic" in title_lower or "[test fixture]" in title_lower:
        return True

    # 4. Known fixture source identifiers
    if transcript.source_id and transcript.source_id.lower().strip() in TEST_FIXTURE_SOURCE_IDS:
        return True

    return False


def purge_test_fixtures(db: Session) -> int:
    """Safely remove test fixture transcripts and associated chunks from the database.

    Leaves all 50 authentic podcast episodes untouched. Returns the count of deleted transcripts.
    """
    stmt = select(Transcript)
    transcripts = db.execute(stmt).scalars().all()
    count = 0
    for t in transcripts:
        dummy_chunk = t.chunks[0] if t.chunks else None
        if is_synthetic_or_fixture(t, dummy_chunk):
            db.delete(t)
            count += 1
    if count > 0:
        db.commit()
    return count


def search_transcripts(
    db: Session,
    query: str,
    limit: int = 5,
    exclude_synthetic: bool = True,
) -> List[SearchResultItem]:
    """Search transcript chunks using keyword matching and relevance ranking.

    Args:
        db: Active database session.
        query: User search query or keywords.
        limit: Maximum number of ranked chunks to return.
        exclude_synthetic: When True (default for production chat), excludes all
            records marked as synthetic test data or test fixtures. When False,
            includes all records (used for test verification).
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    # Extract distinct alphanumeric search terms with stop word filtering
    stop_words = {
        "in", "on", "at", "to", "for", "of", "by", "with", "from",
        "as", "is", "are", "was", "were", "it", "an", "the", "and",
        "or", "so", "be", "do", "does", "did", "if", "this", "that",
    }
    raw_terms = re.findall(r"\w+", clean_query.lower())
    filtered_terms = [t for t in raw_terms if len(t) >= 2 and t not in stop_words]
    terms = list(dict.fromkeys(filtered_terms if filtered_terms else [t for t in raw_terms if len(t) >= 2]))

    if not terms:
        return []

    # Build SQL filter for candidate chunks matching any query term or phrase
    conditions = []
    # Exact query match candidate
    conditions.append(TranscriptChunk.chunk_text.ilike(f"%{clean_query}%"))
    conditions.append(Transcript.title.ilike(f"%{clean_query}%"))

    for term in terms:
        conditions.append(TranscriptChunk.chunk_text.ilike(f"%{term}%"))
        conditions.append(Transcript.title.ilike(f"%{term}%"))

    stmt = (
        select(TranscriptChunk, Transcript)
        .join(Transcript, TranscriptChunk.transcript_id == Transcript.id)
        .where(or_(*conditions))
    )

    rows = db.execute(stmt).all()

    if not rows:
        return []

    # Score candidates
    scored_results = []
    query_lower = clean_query.lower()

    for chunk, transcript in rows:
        # Exclude synthetic benchmark fixtures from production search
        if exclude_synthetic and is_synthetic_or_fixture(transcript, chunk):
            continue

        chunk_lower = chunk.chunk_text.lower()
        title_lower = transcript.title.lower()

        score = 0.0

        # Exact phrase bonus
        if query_lower in chunk_lower:
            score += 10.0
        if query_lower in title_lower:
            score += 15.0

        # Term frequency bonus
        matched_terms = 0
        for term in terms:
            c_count = chunk_lower.count(term)
            t_count = title_lower.count(term)
            if c_count > 0 or t_count > 0:
                matched_terms += 1
                score += c_count * 2.0
                score += t_count * 4.0

        # Coverage bonus (% of query terms found)
        coverage_ratio = matched_terms / len(terms)
        score += coverage_ratio * 5.0

        # Build metadata payload
        merged_meta = {}
        if isinstance(transcript.meta_info, dict):
            merged_meta.update(transcript.meta_info)
        if isinstance(chunk.meta_info, dict):
            merged_meta.update(chunk.meta_info)

        item = SearchResultItem(
            chunk_id=chunk.id,
            transcript_id=transcript.id,
            transcript_title=transcript.title,
            source_filename=transcript.source_filename,
            chunk_index=chunk.chunk_index,
            chunk_text=chunk.chunk_text,
            score=round(score, 2),
            metadata=merged_meta,
        )
        scored_results.append(item)

    # Sort by relevance score descending, then chunk_index ascending
    scored_results.sort(key=lambda x: (-x.score, x.chunk_index))

    return scored_results[:limit]
