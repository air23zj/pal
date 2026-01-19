"""MCP Connectors for Google Workspace"""
from .base import BaseConnector, ConnectorResult
from .gmail import GmailConnector
from .calendar import CalendarConnector
from .tasks import TasksConnector

__all__ = [
    "BaseConnector",
    "ConnectorResult",
    "GmailConnector",
    "CalendarConnector",
    "TasksConnector",
]
