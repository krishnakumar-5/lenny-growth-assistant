from datetime import datetime, timezone
import logging
from typing import Any, Dict, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.conversation import ConversationSession, Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageItem,
    SessionDetail,
    SessionRenameRequest,
    SessionSummary,
)
from app.services.agent.grounded_agent import GroundedGrowthAgent
from app.services.agent.pi_agent_adapter import (
    PiAgentExecutionError,
    PiAgentTimeoutError,
    PiAgentUnavailableError,
)
from app.services.llm import (
    CloudProviderConfigurationError,
    LLMGenerationError,
    OllamaModelNotFoundError,
    OllamaUnavailableError,
    get_llm_client,
)

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Grounded Chat with Growth Assistant",
    description=(
        "Interact with The Lenny Growth Assistant. Queries the podcast knowledge base, "
        "enforces evidence-based grounding, persists conversation turns in the database, "
        "and returns structured source citations."
    ),
)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a chat message, execute agent retrieval, and persist session history."""
    # 1. Resolve or create ConversationSession
    session: ConversationSession
    if request.session_id:
        stmt = select(ConversationSession).where(ConversationSession.id == request.session_id)
        existing_session = db.execute(stmt).scalar_one_or_none()
        if not existing_session:
            logger.warning("Session ID not found: %s", request.session_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found.",
            )
        session = existing_session
    else:
        # Create new session
        summary_title = request.message.strip()
        if len(summary_title) > 50:
            summary_title = summary_title[:47] + "..."
        session = ConversationSession(
            title=summary_title or "New Conversation",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # 2. Retrieve recent session history (enforcing strict session isolation)
    history_stmt = (
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
    )
    raw_history = db.execute(history_stmt).scalars().all()
    conversation_history: List[Dict[str, str]] = [
        {"role": m.role, "content": m.content}
        for m in raw_history[-settings.MAX_HISTORY_TURNS:]
    ]

    # 3. Persist user turn
    user_msg = Message(
        session_id=session.id,
        role="user",
        content=request.message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)
    db.commit()

    # 4. Resolve LLM provider client
    try:
        llm_client = get_llm_client(
            provider_name=request.provider,
            model_name=request.model,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 5. Execute Grounded Growth Agent
    agent = GroundedGrowthAgent(
        llm_client=llm_client,
        agent_framework=request.agent_framework or settings.AGENT_FRAMEWORK,
    )

    try:
        agent_result = await agent.run(
            db=db,
            user_message=request.message,
            conversation_history=conversation_history,
        )
    except PiAgentUnavailableError as e:
        logger.error("Pi Coding Agent unavailable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except PiAgentTimeoutError as e:
        logger.error("Pi Coding Agent timed out: %s", e)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e),
        )
    except PiAgentExecutionError as e:
        logger.error("Pi Coding Agent runtime failure: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pi Coding Agent runtime failure: {str(e)}",
        )
    except OllamaUnavailableError as e:
        logger.error("Ollama connection failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Local Ollama service is unavailable at '{settings.OLLAMA_BASE_URL}'. "
                "Please verify that Ollama is running ('ollama serve') and accessible."
            ),
        )
    except OllamaModelNotFoundError as e:
        logger.error("Ollama model missing: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except CloudProviderConfigurationError as e:
        logger.error("Anthropic cloud provider misconfigured: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except LLMGenerationError as e:
        logger.error("LLM generation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream LLM generation failure: {str(e)}",
        )
    except Exception as e:
        logger.error("Unhandled error in chat endpoint: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the assistant response.",
        )

    # 6. Persist assistant turn
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=agent_result.response_text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(assistant_msg)
    # Touch session updated_at
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant_msg)

    # 7. Construct and return structured response
    return ChatResponse(
        session_id=session.id,
        message=agent_result.response_text,
        role="assistant",
        provider=agent_result.provider,
        model=agent_result.model,
        agent_framework=agent_result.agent_framework,
        sources=agent_result.citations,
        insufficient_evidence=agent_result.insufficient_evidence,
        created_at=assistant_msg.created_at,
    )


@router.get(
    "/chat/sessions",
    response_model=List[SessionSummary],
    status_code=status.HTTP_200_OK,
    summary="List Saved Conversation Sessions",
    description="Returns all conversation sessions ordered by updated_at descending with message counts and last message previews.",
)
def list_sessions(db: Session = Depends(get_db)) -> List[SessionSummary]:
    """Retrieve all saved conversation sessions with summary metadata."""
    stmt = select(ConversationSession).order_by(ConversationSession.updated_at.desc())
    sessions = db.execute(stmt).scalars().all()
    results: List[SessionSummary] = []
    for s in sessions:
        msgs = s.messages
        last_msg = msgs[-1].content if msgs else None
        if last_msg and len(last_msg) > 90:
            last_msg = last_msg[:87] + "..."
        results.append(
            SessionSummary(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=len(msgs),
                last_message=last_msg,
            )
        )
    return results


@router.get(
    "/chat/sessions/{session_id}",
    response_model=SessionDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Conversation Session Detail & Messages",
    description="Loads a specific conversation session and all its messages in chronological order.",
)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> SessionDetail:
    """Retrieve complete message history for an individual conversation session."""
    stmt = select(ConversationSession).where(ConversationSession.id == session_id)
    session = db.execute(stmt).scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{session_id}' not found.",
        )
    messages = [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in session.messages
    ]
    return SessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages,
    )


@router.delete(
    "/chat/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Conversation Session",
    description="Deletes a conversation session and cascades deletion to all associated messages.",
)
def delete_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a conversation session by UUID."""
    stmt = select(ConversationSession).where(ConversationSession.id == session_id)
    session = db.execute(stmt).scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{session_id}' not found.",
        )
    db.delete(session)
    db.commit()
    return {"status": "deleted", "session_id": str(session_id)}


@router.patch(
    "/chat/sessions/{session_id}",
    response_model=SessionSummary,
    status_code=status.HTTP_200_OK,
    summary="Rename Conversation Session",
    description="Updates the title of an existing conversation session.",
)
def rename_session(
    session_id: uuid.UUID,
    payload: SessionRenameRequest,
    db: Session = Depends(get_db),
) -> SessionSummary:
    """Update title for a conversation session."""
    stmt = select(ConversationSession).where(ConversationSession.id == session_id)
    session = db.execute(stmt).scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{session_id}' not found.",
        )
    session.title = payload.title
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    msgs = session.messages
    last_msg = msgs[-1].content if msgs else None
    if last_msg and len(last_msg) > 90:
        last_msg = last_msg[:87] + "..."
    return SessionSummary(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(msgs),
        last_message=last_msg,
    )
