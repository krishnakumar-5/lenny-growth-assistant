import re
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


def generate_mock_markdown_essay(
    title: str = "Stop Obsessing Over Top-of-Funnel Acquisition",
    hook: str = "Most early founders obsess over acquisition while their product bleeds users out the door.",
    target_body_words: int = 1250,
    include_sources_section: bool = False,
) -> str:
    """Generate structured markdown essay with exact body word count for testing."""
    sections = [
        "## 1. The Core Problem: The Leaky Bucket Fallacy",
        "## 2. The Grounded Framework: Retention Precedes Acquisition",
        "## 3. Real-World Applications: The 14-Day Reverse Trial",
        "## 4. The 30-Day Tactical Playbook and Concluding Takeaway",
    ]
    # Use unhyphenated single-token vocabulary words to ensure exact 1-to-1 word counting
    vocab = [
        "retention", "cohort", "activation", "growth", "monetization",
        "mechanisms", "compound", "baseline", "expansion", "operating",
        "framework", "metrics", "sustainable", "execution", "discipline",
        "onboarding", "churn", "flywheel", "efficiency", "milestone"
    ]

    skill = Ship30EssaySkill(None)

    if target_body_words < 100:
        body_blocks = [" ".join(vocab[i % len(vocab)] for i in range(target_body_words))]
    else:
        body_blocks = [hook]
        for s in sections:
            body_blocks.append(s)
            body_blocks.append("- **Primary rule**: Implement disciplined cohort accounting before scaling marketing spend.")

        skeleton = "\n\n".join(body_blocks)
        cur_wc = skill._count_body_words(skeleton)
        needed = target_body_words - cur_wc
        if needed > 0:
            filler = " ".join(vocab[i % len(vocab)] for i in range(needed))
            body_blocks.append(f"### Detailed Tactical Mechanics\n\n{filler}")
            # Recompute to account for the subheader words
            new_skeleton = "\n\n".join(body_blocks)
            new_wc = skill._count_body_words(new_skeleton)
            diff = target_body_words - new_wc
            if diff != 0:
                # Adjust filler
                adjusted_needed = needed + diff
                body_blocks[-1] = f"### Detailed Tactical Mechanics\n\n{' '.join(vocab[i % len(vocab)] for i in range(adjusted_needed))}"

    body_text = "\n\n".join(body_blocks)
    full_text = f"# {title}\n\n{body_text}"

    if include_sources_section:
        full_text += "\n\n## Sources\n- Source 1: Elena Verna on PLG\n- Source 2: Lenny Rachitsky"

    return full_text


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
        source_id="elena_verna_authentic_sample",
        title="Elena Verna on Product-Led Growth",
        source_filename="elena_verna_plg_interview.md",
        content_hash="hash123",
        raw_content=raw_text,
        meta_info={
            "guest": "Elena Verna",
            "episode": 78,
            "post_url": "https://www.lennyspodcast.com/elena-verna-plg",
        },
    )
    session.add(t)
    session.flush()

    c = TranscriptChunk(
        transcript_id=t.id,
        chunk_index=0,
        chunk_text=raw_text,
        char_count=len(raw_text),
        meta_info={
            "guest": "Elena Verna",
            "episode": 78,
            "post_url": "https://www.lennyspodcast.com/elena-verna-plg",
            "start_char": 0,
            "end_char": len(raw_text),
        },
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
    client.model_name = "qwen2.5:3b"
    mock_essay_output = generate_mock_markdown_essay(
        title="Stop Obsessing Over Top-of-Funnel Acquisition",
        target_body_words=1250,
    )
    client.generate_response.return_value = mock_essay_output
    return client


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_successful_longform_generation(db_session, mock_llm_client):
    skill = Ship30EssaySkill(llm_client=mock_llm_client)
    req = Ship30Request(topic="Elena Verna retention leaky bucket")

    response = await skill.generate_essay(db=db_session, request=req)

    assert "Stop Obsessing Over Top-of-Funnel Acquisition" in response.title
    assert "Elena Verna" in response.guest_attribution
    assert 1150 <= response.word_count <= 1350
    assert response.within_constraints is True
    assert len(response.sources) >= 1
    assert "Elena Verna on Product-Led Growth" in response.sources[0].transcript_title
    assert response.sources[0].metadata.get("post_url") == "https://www.lennyspodcast.com/elena-verna-plg"

    # Check HTML artifact structure and entity encoding
    assert "<!DOCTYPE html>" in response.content_html
    assert "Ship 30 for 30 &bull; Growth Essay" in response.content_html
    assert "â€¢" not in response.content_html  # Verify no mojibake
    assert "<h2" in response.content_html
    assert "<ul" in response.content_html
    assert "<li" in response.content_html
    assert "https://www.lennyspodcast.com/elena-verna-plg" in response.content_html


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_word_count_below_range_flagged(db_session):
    client = AsyncMock(spec=BaseLLMClient)
    client.provider_name = "ollama"
    client.model_name = "qwen2.5:3b"
    # Return 400 words (well below 1,150)
    short_essay = generate_mock_markdown_essay(target_body_words=400)
    client.generate_response.return_value = short_essay

    skill = Ship30EssaySkill(llm_client=client)
    req = Ship30Request(topic="Elena Verna retention leaky bucket")

    response = await skill.generate_essay(db=db_session, request=req)

    assert response.word_count < 1150
    assert response.within_constraints is False
    assert "Outside 1,150&ndash;1,350w target" in response.content_html


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_bounded_retry_succeeds(db_session):
    client = AsyncMock(spec=BaseLLMClient)
    client.provider_name = "ollama"
    client.model_name = "qwen2.5:3b"

    short_draft = generate_mock_markdown_essay(target_body_words=500)
    compliant_draft = generate_mock_markdown_essay(target_body_words=1250)

    # First call returns short draft; retry call returns compliant 1,250-word draft
    client.generate_response.side_effect = [short_draft, compliant_draft]

    skill = Ship30EssaySkill(llm_client=client)
    req = Ship30Request(topic="Elena Verna retention leaky bucket")

    response = await skill.generate_essay(db=db_session, request=req)

    assert client.generate_response.call_count == 2  # Proves bounded retry executed exactly once
    assert 1150 <= response.word_count <= 1350
    assert response.within_constraints is True


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_title_and_sources_excluded_from_word_count(db_session):
    client = AsyncMock(spec=BaseLLMClient)
    client.provider_name = "ollama"
    client.model_name = "qwen2.5:3b"

    test_output = generate_mock_markdown_essay(
        title="Ten Word Long Headline That Must Not Count In Word Count",
        target_body_words=1200,
        include_sources_section=True,
    )
    client.generate_response.return_value = test_output

    skill = Ship30EssaySkill(llm_client=client)
    req = Ship30Request(topic="Elena Verna retention leaky bucket")

    response = await skill.generate_essay(db=db_session, request=req)

    assert response.title == "Ten Word Long Headline That Must Not Count In Word Count"
    assert response.word_count == 1200
    assert response.within_constraints is True


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_html_escaping_and_security(db_session):
    client = AsyncMock(spec=BaseLLMClient)
    client.provider_name = "ollama"
    client.model_name = "qwen2.5:3b"

    xss_markdown = (
        "# <script>alert('xss-title')</script>\n\n"
        "Opening paragraph with **bold metric** and <img src=x onerror=alert('xss-img')>.\n\n"
        "## <iframe src='http://evil.com'></iframe>\n\n"
        "- Bullet with <svg onload=alert(1)> and **strong insight**.\n\n"
        + " ".join(["retention"] * 1220)
    )
    client.generate_response.return_value = xss_markdown

    skill = Ship30EssaySkill(llm_client=client)
    req = Ship30Request(topic="Elena Verna retention leaky bucket")

    response = await skill.generate_essay(db=db_session, request=req)

    # Ensure dangerous tags are escaped and not rendered executable
    assert "<script>" not in response.content_html
    assert "<img src=x" not in response.content_html
    assert "<iframe" not in response.content_html
    assert "<svg" not in response.content_html
    assert "&lt;script&gt;" in response.content_html
    assert "&lt;img" in response.content_html
    assert "&lt;iframe" in response.content_html

    # Ensure legitimate formatting tags ARE rendered
    assert "<strong>bold metric</strong>" in response.content_html
    assert "<strong>strong insight</strong>" in response.content_html
    assert "Ship 30 for 30 &bull; Growth Essay" in response.content_html


@pytest.mark.unit
@pytest.mark.anyio
async def test_ship30_skill_excludes_synthetic_fixtures(db_session):
    # Add a synthetic fixture with a unique topic not present in any other transcript
    raw_fixture = "XyloZebraSyntheticMechanism: Loop multiplier is 3x unverified fixture."
    fixture_t = Transcript(
        source_id="synthetic_fixture_only",
        title="[SYNTHETIC TEST FIXTURE] Fake Growth Loops",
        source_filename="fake_fixture.md",
        content_hash="fake123",
        raw_content=raw_fixture,
        meta_info={"is_test_fixture": True, "synthetic_test_data": True},
    )
    db_session.add(fixture_t)
    db_session.flush()

    fixture_chunk = TranscriptChunk(
        transcript_id=fixture_t.id,
        chunk_index=0,
        chunk_text=raw_fixture,
        char_count=len(raw_fixture),
        meta_info={"is_test_fixture": True, "synthetic_test_data": True},
    )
    db_session.add(fixture_chunk)
    db_session.commit()

    client = AsyncMock(spec=BaseLLMClient)
    skill = Ship30EssaySkill(llm_client=client)
    req = Ship30Request(topic="XyloZebraSyntheticMechanism")

    # Under strict exclusion, synthetic fixtures are rejected and insufficient evidence is raised
    with pytest.raises(InsufficientTranscriptEvidenceError):
        await skill.generate_essay(db=db_session, request=req)

    client.generate_response.assert_not_called()


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
                json={"topic": "Elena Verna retention", "provider": "ollama", "model": "qwen2.5:3b"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["title"] == "Stop Obsessing Over Top-of-Funnel Acquisition"
            assert data["guest_attribution"] == "Elena Verna"
            assert 1150 <= data["word_count"] <= 1350
            assert data["within_constraints"] is True
            assert len(data["sources"]) == 1
            assert data["sources"][0]["metadata"]["post_url"] == "https://www.lennyspodcast.com/elena-verna-plg"
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
