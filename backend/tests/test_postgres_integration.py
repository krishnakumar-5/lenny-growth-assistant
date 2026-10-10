"""Integration tests for live PostgreSQL database persistence.

These tests are marked with @pytest.mark.integration and will only execute when
a reachable PostgreSQL server is detected (either via TEST_DATABASE_URL or the
default PostgreSQL connection settings). When PostgreSQL is offline, these tests
are safely skipped without failing the fast unit test suite.
"""

import os
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import check_db_connection
from app.models import ConversationSession, Message

settings = get_settings()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.sync_database_url)


def is_live_postgres_available() -> bool:
    """Check if a live PostgreSQL test instance is currently accessible."""
    if "postgres" not in TEST_DATABASE_URL:
        return False
    try:
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"connect_timeout": 2},
        )
        return check_db_connection(engine)
    except Exception:
        return False


postgres_available = is_live_postgres_available()


@pytest.fixture(scope="module")
def postgres_live_session():
    """Module-scoped PostgreSQL session with isolated test tables."""
    if not postgres_available:
        pytest.skip("PostgreSQL test instance is not reachable")

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"connect_timeout": 2},
    )

    # Create tables in PostgreSQL
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        # Clean up test tables to avoid polluting database
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.mark.integration
@pytest.mark.skipif(not postgres_available, reason="Live PostgreSQL test server is not available")
def test_postgres_integration_session_lifecycle(postgres_live_session):
    """[Integration/PostgreSQL] Verify session lifecycle and UUID handling in real PostgreSQL."""
    session = ConversationSession(title="Live Postgres Integration Test")
    postgres_live_session.add(session)
    postgres_live_session.commit()
    postgres_live_session.refresh(session)

    assert isinstance(session.id, uuid.UUID)
    assert session.title == "Live Postgres Integration Test"
    assert session.created_at.tzinfo is not None

    msg = Message(
        session_id=session.id,
        role="user",
        content="Testing real PostgreSQL persistence",
    )
    postgres_live_session.add(msg)
    postgres_live_session.commit()
    postgres_live_session.refresh(msg)

    assert isinstance(msg.id, uuid.UUID)
    assert msg.session_id == session.id

    # Verify relationship query
    loaded = postgres_live_session.execute(
        select(ConversationSession).where(ConversationSession.id == session.id)
    ).scalar_one()
    assert len(loaded.messages) == 1
    assert loaded.messages[0].content == "Testing real PostgreSQL persistence"
