import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.transcript import Transcript, TranscriptChunk
from app.services.retrieval import is_synthetic_or_fixture, purge_test_fixtures, search_transcripts


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


@pytest.mark.unit
def test_search_transcripts_excludes_synthetic_fixtures_by_default(db_session_with_data):
    """Regression test: search_transcripts excludes synthetic fixtures by default, but allows them when exclude_synthetic=False."""
    # Seed synthetic benchmark transcript
    synthetic_transcript = Transcript(
        source_id="sample_growth_accounting",
        title="[SYNTHETIC TEST] The Hierarchy of Growth and Retention Accounting",
        source_filename="sample_growth_accounting.md",
        content_hash="synthetic_hash_999",
        raw_content="Synthetic benchmark testing growth accounting loops.",
        meta_info={"synthetic_test_data": True, "is_test_fixture": True},
    )
    synthetic_chunk = TranscriptChunk(
        transcript=synthetic_transcript,
        chunk_index=0,
        chunk_text="Growth accounting decomposes active user cohorts into new and churned.",
        char_count=70,
        meta_info={"synthetic_test_data": True},
    )
    db_session_with_data.add_all([synthetic_transcript, synthetic_chunk])
    db_session_with_data.commit()

    # 1. Default production search (exclude_synthetic=True) must NOT return the synthetic fixture
    results_production = search_transcripts(db_session_with_data, query="Growth accounting", limit=5, exclude_synthetic=True)
    assert not any(r.source_filename == "sample_growth_accounting.md" for r in results_production)
    assert not any(r.transcript_title.startswith("[SYNTHETIC") for r in results_production)

    # 2. Test search with exclude_synthetic=False allows automated tests to inspect fixtures
    results_test = search_transcripts(db_session_with_data, query="Growth accounting", limit=5, exclude_synthetic=False)
    assert any(r.source_filename == "sample_growth_accounting.md" for r in results_test)


@pytest.mark.unit
def test_api_search_excludes_synthetic_unless_explicitly_requested(db_session_with_data):
    """Regression test: POST /api/v1/sources/search excludes synthetic fixtures by default."""
    # Seed synthetic fixture
    t_syn = Transcript(
        source_id="elena_verna_plg",
        title="[TEST FIXTURE] The Ultimate Guide to PLG",
        source_filename="elena_verna_plg.md",
        content_hash="fixture_hash_888",
        raw_content="Product-led growth framework benchmark.",
        meta_info={"is_test_fixture": True, "synthetic_test_data": True},
    )
    c_syn = TranscriptChunk(
        transcript=t_syn,
        chunk_index=0,
        chunk_text="Reverse trial downgrades users gracefully to permanent free.",
        char_count=60,
        meta_info={"is_test_fixture": True},
    )
    db_session_with_data.add_all([t_syn, c_syn])
    db_session_with_data.commit()

    app.dependency_overrides[get_db] = lambda: db_session_with_data
    client = TestClient(app)

    try:
        # Default API request (include_synthetic defaults to False)
        res_default = client.post("/api/v1/sources/search", json={"query": "Reverse trial"})
        assert res_default.status_code == 200
        data_default = res_default.json()
        assert not any(item["source_filename"] == "elena_verna_plg.md" for item in data_default["results"])

        # Explicit test request requesting synthetic fixtures
        res_explicit = client.post("/api/v1/sources/search", json={"query": "Reverse trial", "include_synthetic": True})
        assert res_explicit.status_code == 200
        data_explicit = res_explicit.json()
        assert any(item["source_filename"] == "elena_verna_plg.md" for item in data_explicit["results"])
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
def test_purge_test_fixtures(db_session_with_data):
    """Regression test: purge_test_fixtures deletes only synthetic fixtures and preserves authentic episodes."""
    t_syn = Transcript(
        source_id="brian_balfour_loops",
        title="[TEST FIXTURE] Growth Loops",
        source_filename="brian_balfour_loops.md",
        content_hash="fixture_hash_777",
        raw_content="Loop mechanics.",
        meta_info={"is_test_fixture": True},
    )
    c_syn = TranscriptChunk(
        transcript=t_syn,
        chunk_index=0,
        chunk_text="Loops compound.",
        char_count=15,
        meta_info={},
    )
    db_session_with_data.add_all([t_syn, c_syn])
    db_session_with_data.commit()

    initial_total = db_session_with_data.query(Transcript).count()
    purged_count = purge_test_fixtures(db_session_with_data)

    assert purged_count == 1
    remaining_total = db_session_with_data.query(Transcript).count()
    assert remaining_total == initial_total - 1

    # Verified transcripts must remain untouched
    retention_guide = db_session_with_data.query(Transcript).filter(Transcript.source_id == "retention_guide").first()
    assert retention_guide is not None
    assert retention_guide.title == "Elena Verna on B2B Growth Loops"
