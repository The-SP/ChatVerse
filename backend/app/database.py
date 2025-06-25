from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings
from .logger import init_logger

logger = init_logger(__name__)

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Standard dependency for HTTP endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Context manager for manual database operations
@contextmanager
def get_db_context():
    """
    Context manager for database operations that need manual session management.
    Use this in WebSocket handlers and other long-lived operations.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


# Function to get a new database session (for WebSocket operations)
def get_new_db_session():
    """
    Get a new database session that must be manually closed.
    Only use this when you can't use the dependency injection or context manager.
    """
    return SessionLocal()
