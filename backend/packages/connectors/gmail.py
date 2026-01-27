"""
Gmail MCP Connector
Fetches emails via Google Gmail API
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import base64
import re
import logging

logger = logging.getLogger(__name__)

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import BaseConnector, ConnectorResult


# Gmail API scopes - readonly only
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailConnector(BaseConnector):
    """
    Connector for Gmail via Google API.
    Fetches emails and normalizes them to a standard format.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gmail connector with optional API key (not used for OAuth)."""
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "gmail"

    def is_available(self) -> bool:
        """Check if Gmail integration is available (credentials exist)."""
        creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/gmail_credentials.json")
        return os.path.exists(creds_path)

    async def connect(self) -> bool:
        """
        Authenticate and connect to Gmail API.
        Uses OAuth 2.0 flow with stored credentials.
        """
        creds = None
        token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/gmail_token.json")
        creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/gmail_credentials.json")
        
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
            self._service = build('gmail', 'v1', credentials=creds)
            # Test connection
            self._service.users().getProfile(userId='me').execute()
            return True
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return False
    
    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 50,
        **kwargs
    ) -> ConnectorResult:
        """
        Fetch emails from Gmail.
        
        Args:
            since: Fetch emails after this timestamp
            limit: Maximum number of emails to fetch
            **kwargs: Additional parameters (query, labels, etc.)
        
        Returns:
            ConnectorResult with normalized email data
        """
        if not self.is_connected():
            connected = await self.connect()
            if not connected:
                return ConnectorResult(
                    source=self.source_name,
                    items=[],
                    status="error",
                    error_message="Failed to connect to Gmail",
                    fetched_at=datetime.now(timezone.utc),
                    since_timestamp=since,
                )
        
        try:
            # Build query
            query_parts = []
            
            # Add time filter
            if since:
                # Gmail uses Unix timestamp
                after_timestamp = int(since.timestamp())
                query_parts.append(f"after:{after_timestamp}")
            
            # Add custom query if provided
            if 'query' in kwargs:
                query_parts.append(kwargs['query'])
            else:
                # Default: unread or important in inbox
                query_parts.append("(is:unread OR is:important) in:inbox")
            
            query = ' '.join(query_parts)
            
            # Fetch message list
            results = self._service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            # Fetch full message details
            items = []
            for msg in messages[:limit]:
                try:
                    full_msg = self._service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    normalized = self._normalize_message(full_msg)
                    if normalized:
                        items.append(normalized)
                        
                except HttpError as e:
                    logger.warning(f"Error fetching message {msg['id']}: {e}")
                    continue
            
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
    
    def _normalize_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize Gmail message to standard format.
        
        Returns:
            Normalized message dict or None if parsing fails
        """
        try:
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            
            # Extract body
            body = self._get_message_body(message['payload'])
            
            # Parse date
            internal_date = int(message['internalDate']) / 1000  # Convert ms to seconds
            timestamp = datetime.fromtimestamp(internal_date, tz=timezone.utc)
            
            return {
                "source_id": message['id'],
                "type": "email",
                "timestamp_utc": timestamp.isoformat(),
                "from": headers.get('From', 'Unknown'),
                "to": headers.get('To', ''),
                "subject": headers.get('Subject', '(No subject)'),
                "snippet": message.get('snippet', ''),
                "body": body,
                "labels": message.get('labelIds', []),
                "thread_id": message.get('threadId'),
                "is_unread": 'UNREAD' in message.get('labelIds', []),
                "is_important": 'IMPORTANT' in message.get('labelIds', []),
                "url": f"https://mail.google.com/mail/u/0/#inbox/{message['id']}",
            }
        except Exception as e:
            logger.warning(f"Error normalizing message: {e}")
            return None
    
    def _get_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract body text from message payload"""
        body = ""
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    # Use HTML as fallback, strip tags
                    data = part['body'].get('data', '')
                    if data:
                        html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        body = re.sub('<[^<]+?>', '', html)  # Simple HTML strip
        else:
            # Single part message
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body.strip()
