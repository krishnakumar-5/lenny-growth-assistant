"""Unit tests for SQLAlchemy models, relationships, and session helpers.

These tests run against an isolated in-memory SQLite database using StaticPool,
ensuring rapid execution without touching live or development data.
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import check_db_connection, get_db
from app.models import ConversationSession, Message


@pytest.fixture(scope="function")
def sqlite_test_session():
    """Create an isolated, in-memory SQLite database session for unit testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable SQLite foreign key enforcement
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create tables in isolated in-memory SQLite
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.mark.unit
def test_unit_create_conversation_session_sqlite(sqlite_test_session):
    """[Unit/SQLite] Verify that a ConversationSession can be created and retrieved."""
    session = ConversationSession(title="Product Led Growth Discussion")
    sqlite_test_session.add(session)
    sqlite_test_session.commit()
    sqlite_test_session.refresh(session)

    assert session.id is not None
    assert isinstance(session.id, uuid.UUID)
    assert session.title == "Product Led Growth Discussion"
    assert session.created_at is not None
    assert session.updated_at is not None
    assert session.messages == []


@pytest.mark.unit
def test_unit_session_message_relationship_sqlite(sqlite_test_session):
    """[Unit/SQLite] Verify one-to-many relationship and ordering between session and messages."""
    session = ConversationSession(title="Retention Strategies")
    sqlite_test_session.add(session)
    sqlite_test_session.commit()

    msg1 = Message(
        session_id=session.id,
        role="user",
        content="How do we measure cohort retention?",
    )
    msg2 = Message(
        session_id=session.id,
        role="assistant",
        content="Cohort retention tracks user groups over uniform time slices.",
    )
    sqlite_test_session.add_all([msg1, msg2])
    sqlite_test_session.commit()

    # Query back the session and check relationships
    retrieved_session = sqlite_test_session.execute(
        select(ConversationSession).where(ConversationSession.id == session.id)
    ).scalar_one()

    assert len(retrieved_session.messages) == 2
    assert retrieved_session.messages[0].role == "user"
    assert retrieved_session.messages[0].content == "How do we measure cohort retention?"
    assert retrieved_session.messages[1].role == "assistant"
    assert retrieved_session.messages[0].session_id == session.id
    assert retrieved_session.messages[1].session.title == "Retention Strategies"


@pytest.mark.unit
def test_unit_cascade_delete_messages_sqlite(sqlite_test_session):
    """[Unit/SQLite] Verify that deleting a session cascades and removes associated messages."""
    session = ConversationSession(title="Temporary Session")
    sqlite_test_session.add(session)
    sqlite_test_session.commit()

    msg = Message(
        session_id=session.id,
        role="user",
        content="This should be deleted when session is deleted.",
    )
    sqlite_test_session.add(msg)
    sqlite_test_session.commit()

    # Ensure message exists
    msg_id = msg.id
    assert sqlite_test_session.get(Message, msg_id) is not None

    # Delete session
    sqlite_test_session.delete(session)
    sqlite_test_session.commit()

    # Verify session and message are gone
    assert sqlite_test_session.get(ConversationSession, session.id) is None
    assert sqlite_test_session.get(Message, msg_id) is None


@pytest.mark.unit
def test_unit_check_db_connection_success_sqlite(sqlite_test_session):
    """[Unit/SQLite] Verify check_db_connection returns True with a healthy session."""
    assert check_db_connection(sqlite_test_session) is True


@pytest.mark.unit
def test_unit_check_db_connection_failure():
    """[Unit/SQLite] Verify check_db_connection returns False when database is unreachable."""
    bad_engine = create_engine(
        "postgresql+psycopg://bad:bad@127.0.0.1:59999/bad",
        connect_args={"connect_timeout": 1},
    )
    assert check_db_connection(bad_engine) is False


@pytest.mark.unit
def test_unit_get_db_generator():
    """[Unit/SQLite] Verify get_db generator yields a session and properly terminates."""
    gen = get_db()
    db = next(gen)
    assert db is not None
    # Generator cleanup
    with pytest.raises(StopIteration):
        next(gen)
