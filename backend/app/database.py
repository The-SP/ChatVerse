from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings
from .logger import init_logger

logger = init_logger(__name__)

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Improved connection pool settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if settings.DATABASE_URL.startswith("sqlite")
        else {}
    ),
    # # Increase pool size for better concurrent handling
    # pool_size=20,  # Number of connections to maintain in the pool
    # max_overflow=30,  # Additional connections that can be created beyond pool_size
    # pool_timeout=60,  # Timeout for getting connection from pool
    # pool_recycle=3600,  # Recycle connections after 1 hour
    # pool_pre_ping=True,  # Validate connections before use
)

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
