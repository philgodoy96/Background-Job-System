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
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides one database session per request.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def create_session() -> Session:
    """
    Create a database session manually.

    Workers will use this because they do not run inside FastAPI requests.
    """
    return SessionLocal()