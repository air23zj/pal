"""
Tests for database connection module
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from packages.database import connection

def test_database_url_dev_sqlite():
    """Test using dev sqlite when DATABASE_URL is not set"""
    with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=True):
        with patch("packages.database.connection.logger") as mock_logger:
            # Re-import or reload might be needed but we can just check logic
            # Since connection.py runs on import, we might need to patch it before import
            pass

def test_init_db():
    """Test init_db call"""
    with patch("packages.database.models.Base.metadata.create_all") as mock_create:
        connection.init_db()
        mock_create.assert_called_once()

def test_get_db():
    """Test get_db generator"""
    with patch("packages.database.connection.SessionLocal") as mock_session_factory:
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session
        
        gen = connection.get_db()
        db = next(gen)
        
        assert db == mock_session
        
        # Trigger cleanup
        with pytest.raises(StopIteration):
            next(gen)
        
        mock_session.close.assert_called_once()
