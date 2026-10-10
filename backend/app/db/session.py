from typing import Generator, Union
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Connection arguments for database dialect
connect_args = {}
if "postgres" in settings.sync_database_url:
    connect_args["connect_timeout"] = 2
elif "sqlite" in settings.sync_database_url:
    connect_args["check_same_thread"] = False

# Lazily configured SQLAlchemy engine
engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    echo=settings.DEBUG,
    connect_args=connect_args,
)

if "sqlite" in settings.sync_database_url:
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory for database operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(target: Union[Session, Engine, None] = None) -> bool:
    """Verify live database connectivity by executing a SELECT 1 query.
    
    Accepts an active Session, Engine, or defaults to the application engine.
    Returns True if database is reachable, False otherwise.
    """
    try:
        active_target = target if target is not None else engine
        if isinstance(active_target, Session):
            active_target.execute(text("SELECT 1"))
        else:
            with active_target.connect() as conn:
                conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return False
