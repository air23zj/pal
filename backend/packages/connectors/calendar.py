"""
Google Calendar MCP Connector
Fetches calendar events via Google Calendar API
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import BaseConnector, ConnectorResult


# Calendar API scopes - readonly only
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class CalendarConnector(BaseConnector):
    """
    Connector for Google Calendar via Google API.
    Fetches calendar events and normalizes them.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Calendar connector with optional API key (not used for OAuth)."""
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "calendar"

    def is_available(self) -> bool:
        """Check if Calendar integration is available (credentials exist)."""
        creds_path = os.getenv("CALENDAR_CREDENTIALS_PATH", "credentials/calendar_credentials.json")
        return os.path.exists(creds_path)

    async def connect(self) -> bool:
        """
        Authenticate and connect to Calendar API.
        Uses OAuth 2.0 flow with stored credentials.
        """
        creds = None
        token_path = os.getenv("CALENDAR_TOKEN_PATH", "credentials/calendar_token.json")
        creds_path = os.getenv("CALENDAR_CREDENTIALS_PATH", "credentials/calendar_credentials.json")
        
        # Load existing token if available
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                logger.warning(f"Error loading credentials: {e}")
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds and os.path.exists(creds_path):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Error in OAuth flow: {e}")
                    return False
            
            # Save credentials for next run
            if creds and os.path.exists(os.path.dirname(token_path) or '.'):
                try:
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.error(f"Error saving credentials: {e}")
        
        if not creds:
            logger.warning("No valid credentials available")
            return False
        
        try:
            self._service = build('calendar', 'v3', credentials=creds)
            # Test connection
            self._service.calendarList().list(maxResults=1).execute()
            return True
        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return False
    
    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 50,
        **kwargs
    ) -> ConnectorResult:
        """
        Fetch calendar events.
        
        Args:
            since: Fetch events after this timestamp (default: now)
            limit: Maximum number of events to fetch
            **kwargs: Additional parameters
                - days_ahead: Number of days to look ahead (default: 2)
                - calendar_id: Specific calendar ID (default: 'primary')
        
        Returns:
            ConnectorResult with normalized event data
        """
        if not self.is_connected():
            connected = await self.connect()
            if not connected:
                return ConnectorResult(
                    source=self.source_name,
                    items=[],
                    status="error",
                    error_message="Failed to connect to Calendar",
                    fetched_at=datetime.now(timezone.utc),
                    since_timestamp=since,
                )
        
        try:
            # Determine time range
            now = datetime.now(timezone.utc)
            time_min = since if since else now
            days_ahead = kwargs.get('days_ahead', 2)
            time_max = now + timedelta(days=days_ahead)
            
            calendar_id = kwargs.get('calendar_id', 'primary')
            
            # Fetch events
            events_result = self._service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Normalize events
            items = []
            for event in events:
                normalized = self._normalize_event(event)
                if normalized:
                    items.append(normalized)
            
            return ConnectorResult(
                source=self.source_name,
                items=items,
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )
            
        except HttpError as error:
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="error",
                error_message=str(error),
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )
    
    def _normalize_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize Calendar event to standard format.
        
        Returns:
            Normalized event dict or None if parsing fails
        """
        try:
            # Parse start time
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:
                # DateTime
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                # All-day event
                start_dt = datetime.fromisoformat(start + 'T00:00:00+00:00')
            
            # Parse end time
            end = event['end'].get('dateTime', event['end'].get('date'))
            if 'T' in end:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            else:
                end_dt = datetime.fromisoformat(end + 'T23:59:59+00:00')
            
            # Calculate duration in minutes
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            
            # Extract attendees
            attendees = []
            for attendee in event.get('attendees', []):
                attendees.append({
                    "email": attendee.get('email'),
                    "name": attendee.get('displayName'),
                    "response": attendee.get('responseStatus'),  # accepted, declined, tentative, needsAction
                    "organizer": attendee.get('organizer', False),
                })
            
            return {
                "source_id": event['id'],
                "type": "event",
                "timestamp_utc": start_dt.isoformat(),
                "title": event.get('summary', '(No title)'),
                "description": event.get('description', ''),
                "location": event.get('location', ''),
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "duration_minutes": duration_minutes,
                "is_all_day": 'date' in event['start'],
                "attendees": attendees,
                "attendee_count": len(attendees),
                "organizer": event.get('organizer', {}).get('email'),
                "status": event.get('status'),  # confirmed, tentative, cancelled
                "url": event.get('htmlLink'),
                "meeting_link": event.get('hangoutLink') or self._extract_meeting_link(event.get('description', '')),
                "reminder_minutes": self._get_reminder_minutes(event.get('reminders', {})),
            }
        except Exception as e:
            logger.warning(f"Error normalizing event: {e}")
            return None
    
    def _extract_meeting_link(self, description: str) -> Optional[str]:
        """Extract meeting link from description"""
        import re
        # Common video meeting patterns
        patterns = [
            r'https://meet\.google\.com/[a-z-]+',
            r'https://zoom\.us/j/\d+',
            r'https://teams\.microsoft\.com/[^\s]+',
        ]
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(0)
        return None
    
    def _get_reminder_minutes(self, reminders: Dict[str, Any]) -> Optional[int]:
        """Get reminder time in minutes"""
        if reminders.get('useDefault'):
            return 30  # Default reminder
        overrides = reminders.get('overrides', [])
        if overrides:
            # Return first reminder
            return overrides[0].get('minutes')
        return None
