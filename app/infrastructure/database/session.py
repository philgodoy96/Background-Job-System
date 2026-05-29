from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    The session is committed explicitly by services/repositories when needed.
    If an exception escapes the request, the session is rolled back.
    """
    session = SessionLocal()

    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_db_session() -> Session:
    """
    Create a database session for non-HTTP runtimes.

    Workers and recovery processes will use this because they do not run inside
    FastAPI dependency injection.
    """
    return SessionLocal()