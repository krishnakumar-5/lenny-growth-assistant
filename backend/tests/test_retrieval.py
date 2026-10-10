import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.transcript import Transcript, TranscriptChunk
from app.services.retrieval import search_transcripts


@pytest.fixture(scope="function")
def db_session_with_data():
    """Create in-memory SQLite database populated with test transcript chunks."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test transcript
    t1 = Transcript(
        source_id="retention_guide",
        title="Elena Verna on B2B Growth Loops",
        source_filename="elena_verna.md",
        content_hash="abc123hash",
        raw_content="Raw text...",
        meta_info={"guest": "Elena Verna", "episode": 42},
    )
    c1 = TranscriptChunk(
        transcript=t1,
        chunk_index=0,
        chunk_text="Cohort retention measures user engagement over uniform time periods.",
        char_count=68,
        meta_info={"start_char": 0, "end_char": 68},
    )
    c2 = TranscriptChunk(
        transcript=t1,
        chunk_index=1,
        chunk_text="Monetization and product pricing tiers must align with user value metrics.",
        char_count=74,
        meta_info={"start_char": 69, "end_char": 143},
    )

    t2 = Transcript(
        source_id="sales_motion",
        title="Enterprise Sales Motion Strategy",
        source_filename="enterprise_sales.md",
        content_hash="def456hash",
        raw_content="Raw text...",
        meta_info={"topic": "Sales"},
    )
    c3 = TranscriptChunk(
        transcript=t2,
        chunk_index=0,
        chunk_text="In enterprise software, the sales team assists self-serve product users.",
        char_count=73,
        meta_info={"start_char": 0, "end_char": 73},
    )

    session.add_all([t1, t2, c1, c2, c3])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.mark.unit
def test_search_transcripts_matching(db_session_with_data):
    """Verify that keyword search returns matching chunks ranked by relevance."""
    results = search_transcripts(db_session_with_data, query="cohort retention", limit=5)

    assert len(results) >= 1
    top = results[0]
    assert "retention" in top.chunk_text.lower()
    assert top.transcript_title == "Elena Verna on B2B Growth Loops"
    assert top.score > 0
    assert top.metadata.get("guest") == "Elena Verna"


@pytest.mark.unit
def test_search_transcripts_title_boost(db_session_with_data):
    """Verify that queries matching transcript titles receive a boost."""
    results = search_transcripts(db_session_with_data, query="Enterprise Sales", limit=5)

    assert len(results) >= 1
    top = results[0]
    assert "Enterprise Sales" in top.transcript_title


@pytest.mark.unit
def test_search_transcripts_empty_results(db_session_with_data):
    """Verify that non-matching queries return an empty list."""
    results = search_transcripts(db_session_with_data, query="cryptocurrency blockchain", limit=5)
    assert results == []


@pytest.mark.unit
def test_search_transcripts_empty_query(db_session_with_data):
    """Verify that empty or whitespace query returns empty list."""
    results = search_transcripts(db_session_with_data, query="   ", limit=5)
    assert results == []


@pytest.mark.unit
def test_api_search_endpoint(db_session_with_data):
    """Verify POST /api/v1/sources/search returns valid response structure."""
    # Override get_db dependency to use the test session
    app.dependency_overrides[get_db] = lambda: db_session_with_data

    client = TestClient(app)
    response = client.post(
        "/api/v1/sources/search",
        json={"query": "cohort retention", "limit": 3},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "cohort retention"
    assert data["total_results"] >= 1
    assert len(data["results"]) <= 3

    item = data["results"][0]
    assert "chunk_id" in item
    assert "transcript_id" in item
    assert "transcript_title" in item
    assert "source_filename" in item
    assert "chunk_index" in item
    assert "chunk_text" in item
    assert "score" in item
    assert "metadata" in item


@pytest.mark.unit
def test_api_search_validation_errors():
    """Verify validation errors for empty query or invalid limit."""
    client = TestClient(app)

    # Empty query
    res1 = client.post("/api/v1/sources/search", json={"query": ""})
    assert res1.status_code == 422

    # Whitespace query
    res2 = client.post("/api/v1/sources/search", json={"query": "   "})
    assert res2.status_code == 422

    # Limit too high
    res3 = client.post("/api/v1/sources/search", json={"query": "retention", "limit": 100})
    assert res3.status_code == 422
