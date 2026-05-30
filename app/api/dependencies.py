from collections.abc import Generator

from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db_session


def get_session() -> Generator[Session, None, None]:
    """
    Provide a database session to API routes.

    This wrapper keeps FastAPI route modules independent from the exact database
    session implementation.
    """
    yield from get_db_session()