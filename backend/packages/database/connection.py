"""Database connection management"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

logger = logging.getLogger(__name__)

# Get database URL from environment - NO default credentials for security
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Check if we're in test mode
    if os.getenv("TESTING") == "true":
        DATABASE_URL = "sqlite:///:memory:"
    else:
        logger.warning(
            "DATABASE_URL not set. Using SQLite for development. "
            "Set DATABASE_URL environment variable for production."
        )
        DATABASE_URL = "sqlite:///./morning_brief_dev.db"

# Create engine with appropriate settings based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration (for tests)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration (for production)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use with FastAPI Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database (create all tables)"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
