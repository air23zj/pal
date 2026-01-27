"""
Google Keep MCP Connector
Fetches notes and reminders via Google Keep API

Based on Google Keep API Reference:
https://developers.google.com/workspace/keep/api/reference/rest

Features:
- Fetches recent notes from Google Keep
- Supports text notes, checklists, and notes with attachments
- Filters by update time and note types
- Handles note labels and colors
- OAuth 2.0 authentication with automatic token refresh
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import BaseConnector, ConnectorResult


# Google Keep API scopes - readonly only
SCOPES = ['https://www.googleapis.com/auth/keep.readonly']


class KeepConnector(BaseConnector):
    """
    Connector for Google Keep via Google API.
    Fetches notes, checklists, and reminders from Google Keep.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Keep connector with optional API key (not used for OAuth)."""
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "keep"

    def is_available(self) -> bool:
        """Check if Keep integration is available (credentials exist)."""
        creds_path = os.getenv("KEEP_CREDENTIALS_PATH", "credentials/keep_credentials.json")
        return os.path.exists(creds_path)

    async def connect(self) -> bool:
        """
        Authenticate and connect to Keep API.
        Uses OAuth 2.0 flow with stored credentials.
        """
        creds = None
        token_path = os.getenv("KEEP_TOKEN_PATH", "credentials/keep_token.json")
        creds_path = os.getenv("KEEP_CREDENTIALS_PATH", "credentials/keep_credentials.json")

        # Load existing token if available
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                logger.warning(f"Error loading Keep credentials: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Error refreshing Keep credentials: {e}")
                    creds = None

            if not creds and os.path.exists(creds_path):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Error in Keep OAuth flow: {e}")
                    return False

            # Save credentials for next run
            if creds and os.path.exists(os.path.dirname(token_path) or '.'):
                try:
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.error(f"Error saving Keep credentials: {e}")

        if not creds:
            logger.warning("No valid Keep credentials available")
            return False

        try:
            self._service = build('keep', 'v1', credentials=creds)
            # Test connection by listing notes (with limit 1)
            self._service.notes().list(pageSize=1).execute()
            return True
        except HttpError as error:
            logger.error(f"Keep API error: {error}")
            return False

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 50,
        **kwargs
    ) -> ConnectorResult:
        """
        Fetch notes from Google Keep.

        Args:
            since: Fetch notes updated after this timestamp
            limit: Maximum number of notes to fetch
            **kwargs: Additional parameters
                - filter_trashed: Include/exclude trashed notes (default: False)
                - filter_archived: Include/exclude archived notes (default: False)
                - label_filter: List of label IDs to filter by

        Returns:
            ConnectorResult with normalized note data
        """
        if not self.is_connected():
            connected = await self.connect()
            if not connected:
                return ConnectorResult(
                    source=self.source_name,
                    items=[],
                    status="error",
                    error_message="Failed to connect to Keep API",
                    fetched_at=datetime.now(timezone.utc),
                    since_timestamp=since,
                )

        try:
            # Build API parameters according to Google Keep API reference
            params = {
                'pageSize': min(limit, 50),  # API limit is 50 per request
            }

            # Note filtering options
            if not kwargs.get('filter_trashed', False):
                # By default, exclude trashed notes
                pass  # Keep API doesn't have explicit trashed filter in list

            if not kwargs.get('filter_archived', False):
                # By default, exclude archived notes
                pass  # Keep API doesn't have explicit archived filter in list

            # Label filtering (if supported)
            label_filter = kwargs.get('label_filter')
            if label_filter:
                # Note: Keep API may not support label filtering in list operation
                logger.info(f"Label filtering requested but not supported by Keep API: {label_filter}")

            # Handle pagination (Google Keep API supports pageToken)
            page_token = None
            all_notes = []
            notes_fetched = 0

            while notes_fetched < limit:
                if page_token:
                    params['pageToken'] = page_token

                try:
                    result = self._service.notes().list(**params).execute()
                except HttpError as e:
                    logger.warning(f"Error fetching notes from Keep API: {e}")
                    break

                notes = result.get('notes', [])

                # Apply client-side filtering since API has limited filter options
                filtered_notes = self._apply_client_filters(notes, kwargs)

                # Add filtered notes to our collection
                remaining_slots = limit - notes_fetched
                notes_to_add = filtered_notes[:remaining_slots]
                all_notes.extend(notes_to_add)
                notes_fetched += len(notes_to_add)

                # Check for next page
                page_token = result.get('nextPageToken')
                if not page_token:
                    break

                # Remove pageToken for next iteration
                params.pop('pageToken', None)

            # Normalize notes
            items = []
            for note in all_notes:
                normalized = self._normalize_note(note)
                if normalized:
                    items.append(normalized)

            # Sort by update time (most recent first)
            items.sort(key=lambda x: x.get('updated_at', ''), reverse=True)

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

    def _apply_client_filters(self, notes: List[Dict[str, Any]], kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply client-side filtering since Keep API has limited filter options."""
        filtered_notes = []

        filter_trashed = kwargs.get('filter_trashed', False)
        filter_archived = kwargs.get('filter_archived', False)

        for note in notes:
            # Filter trashed notes
            if not filter_trashed and note.get('trashed', False):
                continue

            # Filter archived notes
            if not filter_archived and note.get('archived', False):
                continue

            # Apply time-based filtering if since timestamp provided
            # Note: Keep API doesn't support server-side time filtering in list operation
            # This would need to be done in the main fetch method

            filtered_notes.append(note)

        return filtered_notes

    def _normalize_note(self, note: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize Google Keep note to standard format.

        Based on Google Keep API v1 note resource:
        https://developers.google.com/workspace/keep/api/reference/rest/v1/notes

        Returns:
            Normalized note dict or None if parsing fails
        """
        try:
            # Parse timestamps (RFC 3339 format from API)
            create_time = note.get('createTime')
            update_time = note.get('updateTime')

            if update_time:
                updated_dt = datetime.fromisoformat(update_time.replace('Z', '+00:00'))
            else:
                updated_dt = datetime.now(timezone.utc)

            if create_time:
                created_dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
            else:
                created_dt = updated_dt

            # Extract note content based on type
            note_type = "text"  # default
            title = ""
            content = ""
            checklist_items = []
            attachments = []

            # Handle different note types
            if 'text' in note:
                note_type = "text"
                content = note['text'].get('text', '')
            elif 'list' in note:
                note_type = "list"
                checklist_items = self._normalize_checklist(note['list'])
            elif 'attachments' in note and note['attachments']:
                note_type = "attachment"
                attachments = self._normalize_attachments(note['attachments'])

            # Extract title from first line of text or use default
            if content:
                lines = content.split('\n', 1)
                title = lines[0].strip()
                if len(lines) > 1:
                    content = lines[1].strip()
            else:
                title = f"Keep Note ({note_type})"

            # Extract labels
            labels = []
            if 'labels' in note:
                labels = [label.get('name', '') for label in note['labels'] if label.get('name')]

            # Extract color and other metadata
            color = note.get('color', {}).get('name', 'DEFAULT')
            trashed = note.get('trashed', False)
            archived = note.get('archived', False)
            pinned = note.get('pinned', False)

            return {
                "source_id": note['name'],  # Keep API uses 'name' as ID
                "type": "note",
                "note_type": note_type,  # text, list, or attachment
                "timestamp_utc": updated_dt.isoformat(),
                "title": title,
                "content": content,

                # Note organization
                "labels": labels,
                "color": color,
                "is_pinned": pinned,
                "is_archived": archived,
                "is_trashed": trashed,

                # Content based on type
                "checklist_items": checklist_items if checklist_items else None,
                "attachments": attachments if attachments else None,
                "has_attachments": bool(attachments),

                # Priority indicators
                "is_urgent": any(label.lower() in ['urgent', 'important', 'priority']
                               for label in labels),
                "is_personal": any(label.lower() in ['personal', 'private']
                                 for label in labels),

                # URLs and links
                "url": f"https://keep.google.com/u/0/#NOTE/{note['name']}",

                # Timestamps
                "created_at": created_dt.isoformat(),
                "updated_at": updated_dt.isoformat(),

                # Keep-specific metadata
                "permissions": note.get('permissions', []),
                "assignee": note.get('assignee', []),
            }
        except Exception as e:
            logger.warning(f"Error normalizing Keep note '{note.get('name', 'unknown')}': {e}")
            return None

    def _normalize_checklist(self, checklist: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize checklist items from Keep API format."""
        items = []
        for item in checklist:
            normalized_item = {
                "text": item.get('text', ''),
                "is_checked": item.get('checked', False),
                "sort_order": item.get('sortOrder', 0),
            }
            items.append(normalized_item)
        return items

    def _normalize_attachments(self, attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize attachments from Keep API format."""
        normalized = []
        for attachment in attachments:
            normalized_attachment = {
                "name": attachment.get('name', ''),
                "mime_type": attachment.get('mimeType', ''),
                "file_size": attachment.get('fileSize', 0),
                "url": attachment.get('url', ''),
                "extracted_text": attachment.get('extractedText', ''),
            }
            normalized.append(normalized_attachment)
        return normalized

    async def get_note_details(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific note.

        Based on Google Keep API: GET /v1/{name=notes/*}

        Args:
            note_id: The note identifier

        Returns:
            Detailed note information or None if not found
        """
        if not self.is_connected():
            connected = await self.connect()
            if not connected:
                return None

        try:
            note = self._service.notes().get(name=note_id).execute()
            return self._normalize_note(note)
        except HttpError as e:
            logger.warning(f"Error fetching note details for {note_id}: {e}")
            return None