"""MCP Connectors for Google Workspace"""
from .base import BaseConnector, ConnectorResult
from .gmail import GmailConnector
from .calendar import CalendarConnector
from .tasks import TasksConnector
from .keep import KeepConnector
from .research import ResearchConnector
from .news import NewsConnector
from .flights import FlightsConnector
from .dining import DiningConnector
from .travel import TravelConnector
from .local import LocalConnector
from .shopping import ShoppingConnector

__all__ = [
    "BaseConnector",
    "ConnectorResult",
    "GmailConnector",
    "CalendarConnector",
    "TasksConnector",
    "KeepConnector",
    "ResearchConnector",
    "NewsConnector",
    "FlightsConnector",
    "DiningConnector",
    "TravelConnector",
    "LocalConnector",
    "ShoppingConnector",
]
