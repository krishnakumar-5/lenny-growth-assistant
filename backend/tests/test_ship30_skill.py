from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.transcript import Transcript, TranscriptChunk
from app.schemas.ship30 import Ship30Request
from app.services.llm.base import BaseLLMClient, OllamaUnavailableError
from app.services.skills.ship30_skill import (
    InsufficientTranscriptEvidenceError,
    Ship30EssaySkill,
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session fixture."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    raw_text = (
        "Elena Verna explains: The biggest mistake early-stage founders and product managers "
        "make is obsessing over acquisition before retention is solved. You cannot pour water "
        "into a leaky bucket. Product-led growth is fundamentally an operating model where the "
        "product drives acquisition, retention, and monetization. But retention is the absolute "
        "foundation. If your user retention curve does not flatten into a stable baseline, you "
        "do not have product-market fit, and spending marketing dollars is lighting capital on fire."
    )

    t = Transcript(
        source_id="elena_verna_plg_fixture",
        title="Elena Verna on Product-Led Growth",
        source_filename="elena_verna_plg.md",
        content_hash="hash123",
        raw_content=raw_text,
        meta_info={"guest": "Elena Verna", "episode": 78},
    )
    session.add(t)
    session.flush()

    c = TranscriptChunk(
        transcript_id=t.id,
        chunk_index=0,
        chunk_text=raw_text,
        char_count=len(raw_text),
        meta_info={"guest": "Elena Verna", "episode": 78, "start_char": 0, "end_char": len(raw_text)},
    )
    session.add(c)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=BaseLLMClient)
    client.provider_name = "ollama"
    client.model_name = "llama3:8b"
    mock_essay_output = (
        "# Stop Obsessing Over Acquisition\n\n"
        "Most early-stage startups obsess over top-of-funnel acquisition while their product bleeds users out the back door.\n\n"
        "Elena Verna calls this the fatal 'leaky bucket' fallacy. If your retention curve never flattens into a predictable baseline, you do not have product-market fit.\n\n"
        "Here is the authentic growth playbook:\n"
        "- Retention precedes acquisition: Fix the bucket before pouring marketing capital.\n"
        "- The 14-day reverse trial builds habits while letting enterprise features sell themselves.\n"
        "- Product-Qualified Leads (PQLs) bridge self-serve usage into enterprise expansions.\n\n"
        "Audit your 30-day cohort retention curve before spending another marketing dollar today.\n\n"
        "Retention is not just a metric; it is the prerequisite for venture scale."
    )
    client.generate_response.return_value = mock_essay_output
    return client


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_successful_generation(db_session, mock_llm_client):
    skill = Ship30EssaySkill(llm_client=mock_llm_client)
    req = Ship30Request(topic="Elena Verna retention leaky bucket")

    response = await skill.generate_essay(db=db_session, request=req)

    assert "Stop Obsessing Over Acquisition" in response.title
    assert "Elena Verna" in response.guest_attribution
    assert response.word_count > 50
    assert len(response.sources) >= 1
    assert "Elena Verna on Product-Led Growth" in response.sources[0].transcript_title
    assert "<!DOCTYPE html>" in response.content_html
    assert "Ship 30 for 30 • Atomic Essay" in response.content_html


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_insufficient_evidence_raises(db_session, mock_llm_client):
    skill = Ship30EssaySkill(llm_client=mock_llm_client)
    req = Ship30Request(topic="quantum thermodynamics in space")

    with pytest.raises(InsufficientTranscriptEvidenceError) as exc_info:
        await skill.generate_essay(db=db_session, request=req)

    assert "no verified podcast transcripts matched topic" in str(exc_info.value)
    mock_llm_client.generate_response.assert_not_called()


@pytest.mark.unit
def test_ship30_api_endpoint_success(db_session, mock_llm_client):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        with patch("app.api.routes.skills.get_llm_client", return_value=mock_llm_client):
            res = client.post(
                "/api/v1/skills/ship30-essay",
                json={"topic": "Elena Verna retention", "provider": "ollama", "model": "llama3:8b"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["title"] == "Stop Obsessing Over Acquisition"
            assert data["guest_attribution"] == "Elena Verna"
            assert data["word_count"] > 50
            assert len(data["sources"]) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
def test_ship30_api_endpoint_422_on_insufficient_evidence(db_session, mock_llm_client):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        with patch("app.api.routes.skills.get_llm_client", return_value=mock_llm_client):
            res = client.post(
                "/api/v1/skills/ship30-essay",
                json={"topic": "cryptocurrency mining rigs"},
            )
            assert res.status_code == 422
            data = res.json()
            assert "no verified podcast transcripts" in data["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
def test_ship30_api_endpoint_503_on_ollama_unavailable(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        with patch("app.api.routes.skills.get_llm_client") as mock_get_client:
            mock_client = AsyncMock(spec=BaseLLMClient)
            mock_client.generate_response.side_effect = OllamaUnavailableError("Ollama is down")
            mock_get_client.return_value = mock_client

            res = client.post(
                "/api/v1/skills/ship30-essay",
                json={"topic": "Elena Verna retention"},
            )
            assert res.status_code == 503
    finally:
        app.dependency_overrides.clear()
