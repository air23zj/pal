"""
Tests for connectors base module
"""
import pytest
from datetime import datetime, timezone
from packages.connectors.base import ConnectorResult, BaseConnector


class TestConnectorResult:
    """Test ConnectorResult schema"""
    
    def test_connector_result_ok(self):
        """Test creating a successful ConnectorResult"""
        now = datetime.now(timezone.utc)
        result = ConnectorResult(
            source="gmail",
            items=[{"id": "1", "title": "Test"}],
            status="ok",
            fetched_at=now
        )
        assert result.source == "gmail"
        assert len(result.items) == 1
        assert result.status == "ok"
        assert result.error_message is None
    
    def test_connector_result_error(self):
        """Test ConnectorResult with error"""
        now = datetime.now(timezone.utc)
        result = ConnectorResult(
            source="gmail",
            items=[],
            status="error",
            error_message="Connection failed",
            fetched_at=now
        )
        assert result.status == "error"
        assert result.error_message == "Connection failed"
        assert len(result.items) == 0
    
    def test_connector_result_degraded(self):
        """Test ConnectorResult with degraded status"""
        now = datetime.now(timezone.utc)
        result = ConnectorResult(
            source="gmail",
            items=[{"id": "1"}],
            status="degraded",
            error_message="Partial failure",
            fetched_at=now
        )
        assert result.status == "degraded"
        assert len(result.items) == 1
        assert result.error_message is not None
    
    def test_connector_result_with_since(self):
        """Test ConnectorResult with since_timestamp"""
        now = datetime.now(timezone.utc)
        since = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = ConnectorResult(
            source="gmail",
            items=[],
            status="ok",
            fetched_at=now,
            since_timestamp=since
        )
        assert result.since_timestamp == since
    
    def test_connector_result_empty_items(self):
        """Test ConnectorResult with empty items list"""
        now = datetime.now(timezone.utc)
        result = ConnectorResult(
            source="gmail",
            items=[],
            status="ok",
            fetched_at=now
        )
        assert len(result.items) == 0
        assert result.status == "ok"


class TestBaseConnector:
    """Test BaseConnector abstract class"""
    
    def test_base_connector_is_abstract(self):
        """Test that BaseConnector cannot be instantiated"""
        with pytest.raises(TypeError):
            BaseConnector()
    
    def test_base_connector_subclass_must_implement_fetch(self):
        """Test that subclasses must implement fetch method"""
        class IncompleteConnector(BaseConnector):
            pass
        
        with pytest.raises(TypeError):
            IncompleteConnector()
    
    def test_base_connector_valid_subclass(self):
        """Test creating a valid BaseConnector subclass"""
        class TestConnector(BaseConnector):
            @property
            def source_name(self):
                return "test"
            
            def connect(self):
                pass
            
            def fetch(self, user_id: str, since: datetime = None):
                return ConnectorResult(
                    source="test",
                    items=[{"id": "1"}],
                    status="ok",
                    fetched_at=datetime.now(timezone.utc)
                )
        
        connector = TestConnector()
        result = connector.fetch("test_user")
        assert isinstance(result, ConnectorResult)
        assert result.source == "test"
        assert result.status == "ok"
        assert connector.source_name == "test"
    
    def test_base_connector_subclass_with_since(self):
        """Test connector subclass with since parameter"""
        class TestConnector(BaseConnector):
            @property
            def source_name(self):
                return "test"
            
            def connect(self):
                pass
            
            def fetch(self, user_id: str, since: datetime = None):
                return ConnectorResult(
                    source="test",
                    items=[],
                    status="ok",
                    fetched_at=datetime.now(timezone.utc),
                    since_timestamp=since
                )
        
        connector = TestConnector()
        since = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = connector.fetch("test_user", since=since)
        assert result.since_timestamp == since
