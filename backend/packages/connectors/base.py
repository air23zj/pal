"""
Base connector class for MCP integrations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class ConnectorResult(BaseModel):
    """Result from a connector fetch operation"""
    source: str
    items: List[Dict[str, Any]]
    status: str  # ok | degraded | error
    error_message: Optional[str] = None
    fetched_at: datetime
    since_timestamp: Optional[datetime] = None


class BaseConnector(ABC):
    """
    Base class for all MCP connectors.
    Each connector fetches data from a specific source and returns normalized results.
    """
    
    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize connector with credentials.
        
        Args:
            credentials: OAuth credentials or API keys
        """
        self.credentials = credentials
        self._service = None
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the service.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Fetch items from the source.
        
        Args:
            since: Only fetch items newer than this timestamp
            limit: Maximum number of items to fetch
            **kwargs: Additional source-specific parameters
            
        Returns:
            ConnectorResult with fetched items
        """
        pass
    
    async def disconnect(self) -> None:
        """Clean up resources and close connection"""
        self._service = None
    
    def is_connected(self) -> bool:
        """Check if connector is connected"""
        return self._service is not None
