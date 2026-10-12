from unittest.mock import AsyncMock, patch
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.conversation import ConversationSession, Message
from app.models.transcript import Transcript, TranscriptChunk
from app.services.llm.base import (
    CloudProviderConfigurationError,
    LLMGenerationError,
    OllamaModelNotFoundError,
    OllamaUnavailableError,
)


@pytest.fixture(scope="function")
def db_session_with_knowledge_base():
    """In-memory SQLite database populated with transcript chunks and sessions."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Seed verified transcript
    t1 = Transcript(
        source_id="retention_framework",
        title="Elena Verna on B2B Growth Loops",
        source_filename="elena_verna.md",
        content_hash="hash_elena_123",
        raw_content="Cohort retention measures user engagement over uniform time periods.",
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
        chunk_text="Product pricing tiers must align directly with user value metrics.",
        char_count=66,
        meta_info={"start_char": 69, "end_char": 135},
    )

    # Seed synthetic benchmark transcript with explicit disclaimer
    t2 = Transcript(
        source_id="synthetic_growth_benchmark",
        title="Sample Synthetic Growth Benchmark",
        source_filename="sample_growth_accounting.md",
        content_hash="hash_synthetic_456",
        raw_content="Synthetic benchmark data testing acquisition velocity.",
        meta_info={"synthetic_test_data": True, "topic": "Acquisition"},
    )
    c3 = TranscriptChunk(
        transcript=t2,
        chunk_index=0,
        chunk_text="Acquisition velocity measures new signups compounded across active cycles.",
        char_count=74,
        meta_info={"synthetic_test_data": True},
    )

    db.add_all([t1, t2, c1, c2, c3])
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session_with_knowledge_base):
    """FastAPI TestClient with overridden database dependency."""
    app.dependency_overrides[get_db] = lambda: db_session_with_knowledge_base
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# Chat Endpoint Tests
# ============================================================================


@pytest.mark.unit
def test_chat_creates_new_session_and_persists_messages(client, db_session_with_knowledge_base):
    """Verify that omitting session_id creates a new session and persists both message turns."""
    mock_llm_response = (
        "According to Elena Verna, cohort retention measures user engagement over time."
    )

    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = mock_llm_response

        response = client.post(
            "/api/v1/chat",
            json={"message": "What is cohort retention?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        session_id = uuid.UUID(data["session_id"])
        assert data["message"] == mock_llm_response
        assert data["role"] == "assistant"
        assert data["provider"] == "ollama"
        assert data["insufficient_evidence"] is False
        assert len(data["sources"]) >= 1

        # Check DB session
        session = db_session_with_knowledge_base.get(ConversationSession, session_id)
        assert session is not None
        assert "cohort retention" in session.title.lower()

        # Check DB messages
        messages = (
            db_session_with_knowledge_base.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
            )
            .scalars()
            .all()
        )
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "What is cohort retention?"
        assert messages[1].role == "assistant"
        assert messages[1].content == mock_llm_response


@pytest.mark.unit
def test_chat_multi_turn_with_session_isolation(client, db_session_with_knowledge_base):
    """Verify multi-turn history propagation and strict isolation between sessions."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = "Turn 1 answer."

        # Turn 1 for Session A
        res1 = client.post("/api/v1/chat", json={"message": "First question for A"})
        assert res1.status_code == 200
        session_a_id = res1.json()["session_id"]

        # Turn 2 for Session A
        mock_gen.return_value = "Turn 2 answer."
        res2 = client.post(
            "/api/v1/chat",
            json={"message": "Second question for A", "session_id": session_a_id},
        )
        assert res2.status_code == 200
        assert res2.json()["session_id"] == session_a_id

        # Verify Session A has 4 messages
        msgs_a = (
            db_session_with_knowledge_base.execute(
                select(Message).where(Message.session_id == uuid.UUID(session_a_id))
            )
            .scalars()
            .all()
        )
        assert len(msgs_a) == 4

        # Start Session B
        mock_gen.return_value = "Session B answer."
        res_b = client.post("/api/v1/chat", json={"message": "First question for B"})
        assert res_b.status_code == 200
        session_b_id = res_b.json()["session_id"]
        assert session_b_id != session_a_id

        # Verify Session B has only 2 messages (strict isolation)
        msgs_b = (
            db_session_with_knowledge_base.execute(
                select(Message).where(Message.session_id == uuid.UUID(session_b_id))
            )
            .scalars()
            .all()
        )
        assert len(msgs_b) == 2


@pytest.mark.unit
def test_chat_grounded_response_citation_integrity(client):
    """Verify that source citations contain accurate provenance from retrieved chunks."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = "Pricing tiers must align with value metrics."

        res = client.post("/api/v1/chat", json={"message": "product pricing tiers"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["sources"]) >= 1

        citation = data["sources"][0]
        assert "pricing" in citation["chunk_text"].lower()
        assert citation["transcript_title"] == "Elena Verna on B2B Growth Loops"
        assert citation["source_filename"] == "elena_verna.md"
        assert citation["chunk_index"] == 1
        assert citation["score"] > 0
        assert "guest" in citation["metadata"]


@pytest.mark.unit
def test_chat_insufficient_evidence_response(client):
    """Verify that ungrounded queries return an honest refusal without hallucinating."""
    # When query matches no transcripts, LLM should NOT be called at all
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        res = client.post(
            "/api/v1/chat",
            json={"message": "cryptocurrency blockchain smart contracts"},
        )
        assert res.status_code == 200
        data = res.json()

        assert data["insufficient_evidence"] is True
        assert data["sources"] == []
        assert "could not find sufficient information" in data["message"].lower()
        assert "podcast transcripts" in data["message"].lower()
        # Verify LLM was not invoked for non-existent evidence
        assert not mock_gen.called


@pytest.mark.unit
def test_chat_invalid_session_id_returns_404(client):
    """Verify 404 returned when an unknown session_id UUID is supplied."""
    random_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "session_id": random_id},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Conversation session not found."


@pytest.mark.unit
def test_chat_empty_or_whitespace_message_returns_422(client):
    """Verify validation error when message is empty or only whitespace."""
    res1 = client.post("/api/v1/chat", json={"message": ""})
    assert res1.status_code == 422

    res2 = client.post("/api/v1/chat", json={"message": "   \n\t  "})
    assert res2.status_code == 422


@pytest.mark.unit
def test_chat_ollama_unavailable_returns_503(client):
    """Verify 503 Service Unavailable when local Ollama is offline."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.side_effect = OllamaUnavailableError("Ollama offline")
        res = client.post("/api/v1/chat", json={"message": "cohort retention"})
        assert res.status_code == 503
        detail = res.json()["detail"]
        assert "Local Ollama service is unavailable" in detail
        assert "ollama serve" in detail


@pytest.mark.unit
def test_chat_ollama_model_not_found_returns_503(client):
    """Verify 503 Service Unavailable when requested Ollama model is missing."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.side_effect = OllamaModelNotFoundError("Model not pulled")
        res = client.post("/api/v1/chat", json={"message": "cohort retention"})
        assert res.status_code == 503
        assert "Model not pulled" in res.json()["detail"]


@pytest.mark.unit
def test_chat_anthropic_missing_key_returns_400(client, monkeypatch):
    """Verify 400 Bad Request when Anthropic provider is selected without API key."""
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "ANTHROPIC_API_KEY", None)
    res = client.post(
        "/api/v1/chat",
        json={"message": "cohort retention", "provider": "anthropic"},
    )
    assert res.status_code == 400
    assert "Anthropic API key is not configured" in res.json()["detail"]


@pytest.mark.unit
def test_chat_llm_generation_error_returns_502(client):
    """Verify 502 Bad Gateway when LLM generation fails unexpectedly."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.side_effect = LLMGenerationError("Upstream timeout")
        res = client.post("/api/v1/chat", json={"message": "cohort retention"})
        assert res.status_code == 502
        assert "Upstream LLM generation failure" in res.json()["detail"]


@pytest.mark.unit
def test_chat_unsupported_provider_returns_400(client):
    """Verify 400 Bad Request when an invalid provider name is passed."""
    res = client.post(
        "/api/v1/chat",
        json={"message": "cohort retention", "provider": "unsupported_llm"},
    )
    assert res.status_code == 400
    assert "Unsupported LLM provider" in res.json()["detail"]


# ============================================================================
# Pi Coding Agent Chat Integration Tests
# ============================================================================


@pytest.mark.unit
def test_chat_pi_agent_framework_success(client):
    """Verify successful chat turn executing via Pi Coding Agent runtime."""
    with patch(
        "app.services.agent.pi_agent_adapter.PiCodingAgentAdapter.execute_query",
        new_callable=AsyncMock,
    ) as mock_pi:
        mock_pi.return_value = "Pi Agent: Elena Verna defines retention as compounding engagement."

        res = client.post(
            "/api/v1/chat",
            json={"message": "cohort retention", "agent_framework": "pi_coding_agent"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["agent_framework"] == "pi_coding_agent"
        assert data["message"] == "Pi Agent: Elena Verna defines retention as compounding engagement."
        assert len(data["sources"]) >= 1
        assert "retention" in data["sources"][0]["chunk_text"].lower()
        assert mock_pi.called


@pytest.mark.unit
def test_chat_pi_agent_framework_unavailable_returns_503(client):
    """Verify 503 Service Unavailable when Pi runtime CLI is missing."""
    from app.services.agent.pi_agent_adapter import PiAgentUnavailableError

    with patch(
        "app.services.agent.pi_agent_adapter.PiCodingAgentAdapter.execute_query",
        new_callable=AsyncMock,
    ) as mock_pi:
        mock_pi.side_effect = PiAgentUnavailableError("Pi CLI executable not found on PATH.")

        res = client.post(
            "/api/v1/chat",
            json={"message": "cohort retention", "agent_framework": "pi_coding_agent"},
        )
        assert res.status_code == 503
        assert "Pi CLI executable not found" in res.json()["detail"]


@pytest.mark.unit
def test_chat_pi_agent_framework_timeout_returns_504(client):
    """Verify 504 Gateway Timeout when Pi runtime exceeds timeout."""
    from app.services.agent.pi_agent_adapter import PiAgentTimeoutError

    with patch(
        "app.services.agent.pi_agent_adapter.PiCodingAgentAdapter.execute_query",
        new_callable=AsyncMock,
    ) as mock_pi:
        mock_pi.side_effect = PiAgentTimeoutError("Pi process timed out after 30 seconds.")

        res = client.post(
            "/api/v1/chat",
            json={"message": "cohort retention", "agent_framework": "pi_coding_agent"},
        )
        assert res.status_code == 504
        assert "timed out" in res.json()["detail"]


@pytest.mark.unit
def test_chat_pi_agent_framework_execution_error_returns_502(client):
    """Verify 502 Bad Gateway when Pi CLI returns an execution failure."""
    from app.services.agent.pi_agent_adapter import PiAgentExecutionError

    with patch(
        "app.services.agent.pi_agent_adapter.PiCodingAgentAdapter.execute_query",
        new_callable=AsyncMock,
    ) as mock_pi:
        mock_pi.side_effect = PiAgentExecutionError("Exit code 1: Ollama endpoint unreachable.")

        res = client.post(
            "/api/v1/chat",
            json={"message": "cohort retention", "agent_framework": "pi_coding_agent"},
        )
        assert res.status_code == 502
        assert "runtime failure" in res.json()["detail"]


@pytest.mark.unit
def test_chat_pi_agent_empty_retrieval_preserves_sufficiency_gate(client):
    """Verify Pi agent preserves evidence gate and refuses hallucination without calling Pi CLI."""
    with patch(
        "app.services.agent.pi_agent_adapter.PiCodingAgentAdapter.execute_query",
        new_callable=AsyncMock,
    ) as mock_pi:
        res = client.post(
            "/api/v1/chat",
            json={
                "message": "cryptocurrency blockchain staking protocol",
                "agent_framework": "pi_coding_agent",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["insufficient_evidence"] is True
        assert data["sources"] == []
        assert data["agent_framework"] == "pi_coding_agent"
        assert "could not find sufficient information" in data["message"].lower()
        # Verify Pi CLI was NOT invoked when evidence is absent
        assert not mock_pi.called


@pytest.mark.unit
def test_chat_sqlite_live_db_session_and_messages_persisted(tmp_path):
    """Regression test: verify that chat endpoint persists sessions and messages into SQLite."""
    db_file = tmp_path / "test_chat_persist.db"
    test_db_url = f"sqlite:///{db_file.as_posix()}"

    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(bind=test_engine)

    # Seed knowledge base chunk
    with TestingSession() as seed_db:
        t = Transcript(
            source_id="sqlite_test_ep",
            title="Elena Verna Reverse Trial Playbook",
            source_filename="elena_reverse_trial.md",
            content_hash="hash_sqlite_123",
            raw_content="A reverse trial provides full enterprise access for 14 days and then gracefully downgrades to free.",
            meta_info={"guest": "Elena Verna", "episode": 78},
        )
        c = TranscriptChunk(
            transcript=t,
            chunk_index=0,
            chunk_text="A reverse trial provides full enterprise access for 14 days and then gracefully downgrades to free.",
            char_count=98,
            meta_info={"start_char": 0, "end_char": 98},
        )
        seed_db.add_all([t, c])
        seed_db.commit()

    # Create client using TestingSession
    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    test_client = TestClient(app)

    try:
        mock_response = "Elena Verna describes the reverse trial as a 14-day enterprise trial that downgrades to free."
        with patch(
            "app.services.llm.ollama_client.OllamaClient.generate_response",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = mock_response

            # Turn 1: create new session
            res1 = test_client.post(
                "/api/v1/chat",
                json={"message": "What is Elena Verna's reverse trial?"},
            )
            assert res1.status_code == 200
            data1 = res1.json()
            session_id = uuid.UUID(data1["session_id"])
            assert data1["message"] == mock_response
            assert len(data1["sources"]) == 1

            # Verify SQLite persistence
            with TestingSession() as verify_db:
                db_sess = verify_db.get(ConversationSession, session_id)
                assert db_sess is not None
                db_msgs = (
                    verify_db.execute(
                        select(Message)
                        .where(Message.session_id == session_id)
                        .order_by(Message.created_at.asc())
                    )
                    .scalars()
                    .all()
                )
                assert len(db_msgs) == 2
                assert db_msgs[0].role == "user"
                assert db_msgs[1].role == "assistant"

            # Turn 2: follow-up in the same session
            mock_gen.return_value = "It helps because users form product habits without commitment."
            res2 = test_client.post(
                "/api/v1/chat",
                json={
                    "message": "Why does that work so well?",
                    "session_id": str(session_id),
                },
            )
            assert res2.status_code == 200

            # Verify both turns are preserved in SQLite
            with TestingSession() as verify_db:
                db_msgs = (
                    verify_db.execute(
                        select(Message)
                        .where(Message.session_id == session_id)
                        .order_by(Message.created_at.asc())
                    )
                    .scalars()
                    .all()
                )
                assert len(db_msgs) == 4
                assert [m.role for m in db_msgs] == ["user", "assistant", "user", "assistant"]
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()


@pytest.mark.unit
def test_chat_default_model_is_qwen2_5_3b(client):
    """Verify that when no model is explicitly passed in chat payload, default is qwen2.5:3b."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = "Retention is the foundation of growth loops."

        res = client.post(
            "/api/v1/chat",
            json={"message": "cohort retention", "provider": "ollama"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "ollama"
        assert data["model"] == "qwen2.5:3b"


@pytest.mark.unit
def test_chat_excludes_synthetic_fixtures_from_production_citations(client):
    """Regression test: Chat query matching only synthetic test data refuses to cite it and triggers sufficiency gate."""
    # "acquisition velocity" is only present in synthetic fixture t2
    res = client.post(
        "/api/v1/chat",
        json={"message": "What is acquisition velocity and how do signups compound?"},
    )
    assert res.status_code == 200
    data = res.json()

    # Must trigger honest refusal gate because authentic transcripts lack this evidence
    assert data["insufficient_evidence"] is True
    assert data["sources"] == []
    assert "could not find sufficient information in the available podcast transcripts" in data["message"]


@pytest.mark.unit
def test_chat_citations_contain_only_authentic_sources(client):
    """Regression test: When authentic transcripts match, citations contain no synthetic records."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = "Cohort retention measures user engagement over uniform time periods."

        res = client.post(
            "/api/v1/chat",
            json={"message": "Explain cohort retention and pricing tiers"},
        )
        assert res.status_code == 200
        data = res.json()

        assert data["insufficient_evidence"] is False
        assert len(data["sources"]) >= 1

        for citation in data["sources"]:
            meta = citation.get("metadata", {})
            # Must not be marked as synthetic test data or test fixture
            assert meta.get("synthetic_test_data") not in (True, "true")
            assert meta.get("is_test_fixture") not in (True, "true")
            assert not citation["source_filename"].startswith("sample_growth_accounting")
            assert not citation["transcript_title"].startswith("[SYNTHETIC")


@pytest.mark.unit
def test_session_management_api_lifecycle(client):
    """Test session listing, detail retrieval, renaming, and deletion."""
    with patch(
        "app.services.llm.ollama_client.OllamaClient.generate_response",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = "Cohort retention measures user engagement over uniform time periods."

        # 1. Create a session by chatting
        chat_res = client.post(
            "/api/v1/chat",
            json={"message": "First message about cohort retention"},
        )
        assert chat_res.status_code == 200
        session_id = chat_res.json()["session_id"]

        # 2. List sessions
        list_res = client.get("/api/v1/chat/sessions")
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert len(sessions) >= 1
        matched = next((s for s in sessions if s["id"] == session_id), None)
        assert matched is not None
        assert matched["message_count"] == 2  # 1 user + 1 assistant
        assert matched["last_message"] is not None

        # 3. Retrieve session detail with messages in chronological order
        detail_res = client.get(f"/api/v1/chat/sessions/{session_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == session_id
        assert len(detail["messages"]) == 2
        assert detail["messages"][0]["role"] == "user"
        assert detail["messages"][0]["content"] == "First message about cohort retention"
        assert detail["messages"][1]["role"] == "assistant"

        # 4. Rename session
        rename_res = client.patch(
            f"/api/v1/chat/sessions/{session_id}",
            json={"title": "Custom Renamed Growth Session"},
        )
        assert rename_res.status_code == 200
        assert rename_res.json()["title"] == "Custom Renamed Growth Session"

        # 5. Delete session
        del_res = client.delete(f"/api/v1/chat/sessions/{session_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # 6. Verify 404 on deleted session
        get_again = client.get(f"/api/v1/chat/sessions/{session_id}")
        assert get_again.status_code == 404
