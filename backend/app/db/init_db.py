from sqlalchemy.engine import Engine
from app.db.base import Base
from app.models.conversation import ConversationSession, Message  # noqa: F401
from app.models.transcript import Transcript, TranscriptChunk  # noqa: F401


def init_db(engine: Engine) -> None:
    """Initialize database tables using SQLAlchemy declarative metadata."""
    Base.metadata.create_all(bind=engine)
