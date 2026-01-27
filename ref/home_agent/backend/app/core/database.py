from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import URL
from urllib.parse import urlparse
import ssl
import time
from loguru import logger

from .config import settings

def get_database_url() -> URL:
    """Create SQLAlchemy URL with proper configuration."""
    url = settings.SQLALCHEMY_DATABASE_URL
    
    # Parse the URL to check if it's PostgreSQL
    parsed = urlparse(url)
    if parsed.scheme == "postgresql":
        # Add SSL configuration if needed
        query = {}
        if settings.DB_SSL_MODE:
            query["sslmode"] = settings.DB_SSL_MODE
        if settings.DB_SSL_CA:
            query["sslcert"] = settings.DB_SSL_CERT
        if settings.DB_SSL_KEY:
            query["sslkey"] = settings.DB_SSL_KEY
        if settings.DB_SSL_CA:
            query["sslrootcert"] = settings.DB_SSL_CA
            
        return URL.create(
            drivername=parsed.scheme,
            username=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path.lstrip("/"),
            query=query
        )
    
    return URL(url)

def create_database_engine():
    """Create SQLAlchemy engine with proper configuration."""
    url = get_database_url()
    
    # Configure engine arguments
    engine_args = {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "echo": settings.DB_ECHO,
    }
    
    # Add statement timeout if supported by dialect
    parsed = urlparse(str(url))
    if parsed.scheme in ["postgresql", "mysql"]:
        engine_args["connect_args"] = {
            "command_timeout": settings.DB_STATEMENT_TIMEOUT
        }
    
    # Create engine with retry logic
    for attempt in range(settings.DB_CONNECT_RETRIES):
        try:
            engine = create_engine(url, **engine_args)
            # Test connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return engine
        except Exception as e:
            if attempt == settings.DB_CONNECT_RETRIES - 1:
                logger.error(f"Failed to connect to database after {settings.DB_CONNECT_RETRIES} attempts")
                raise
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            time.sleep(settings.DB_CONNECT_RETRY_DELAY)

# Create engine
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database."""
    # Import all models here to ensure they are registered
    from ..models import base  # noqa
    
    # Create tables if they don't exist
    if settings.DB_MIGRATION_ENABLED:
        # Use Alembic migrations
        from alembic import command
        from alembic.config import Config
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    else:
        # Create tables directly
        Base.metadata.create_all(bind=engine)
