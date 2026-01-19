"""
Tests for database connection module
"""
import pytest
from sqlalchemy.orm import Session
from packages.database.connection import engine, SessionLocal, get_db


class TestDatabaseConnection:
    """Test database connection setup"""
    
    def test_engine_exists(self):
        """Test that database engine is created"""
        assert engine is not None
    
    def test_session_local_exists(self):
        """Test that SessionLocal is created"""
        assert SessionLocal is not None
    
    def test_get_db_generator(self):
        """Test get_db dependency generator"""
        db_gen = get_db()
        assert db_gen is not None
        
        # Get the session
        db = next(db_gen)
        assert isinstance(db, Session)
        
        # Close the session
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected
    
    def test_session_creation(self):
        """Test creating a database session"""
        session = SessionLocal()
        assert isinstance(session, Session)
        session.close()
    
    def test_session_context_manager(self):
        """Test session with context manager"""
        with SessionLocal() as session:
            assert isinstance(session, Session)
    
    def test_engine_connection(self):
        """Test engine can create connections"""
        with engine.connect() as conn:
            assert conn is not None
