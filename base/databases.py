import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from settings import settings


logger = logging.getLogger(__name__)


engine = create_engine(
    settings.database_url + "?charset=utf8mb4",
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_context() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exception:
        session.rollback()
        logger.error(f"Database Error: {exception}", exc_info=True)
        raise exception
    finally:
        session.close()
