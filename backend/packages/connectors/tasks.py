"""
Google Tasks MCP Connector
Fetches tasks via Google Tasks API v1

Based on Google Tasks API Reference:
https://developers.google.com/workspace/tasks/reference/rest

Features:
- Fetches tasks from all user tasklists
- Supports filtering by update time, due dates, completion status
- Handles pagination for large task lists
- Provides task prioritization and due date analysis
- OAuth 2.0 authentication with automatic token refresh
- Read-only operations (no task creation/modification)
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


# Tasks API scopes - readonly only
SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']


class TasksConnector(BaseConnector):
    """
    Connector for Google Tasks via Google API.
    Fetches tasks and normalizes them.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Tasks connector with optional API key (not used for OAuth)."""
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "tasks"

    def is_available(self) -> bool:
        """Check if Tasks integration is available (credentials exist)."""
        creds_path = os.getenv("TASKS_CREDENTIALS_PATH", "credentials/tasks_credentials.json")
        return os.path.exists(creds_path)

    async def connect(self) -> bool:
        """
        Authenticate and connect to Tasks API.
        Uses OAuth 2.0 flow with stored credentials.
        """
        creds = None
        token_path = os.getenv("TASKS_TOKEN_PATH", "credentials/tasks_token.json")
        creds_path = os.getenv("TASKS_CREDENTIALS_PATH", "credentials/tasks_credentials.json")
        
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
            self._service = build('tasks', 'v1', credentials=creds)
            # Test connection
            self._service.tasklists().list(maxResults=1).execute()
            return True
        except HttpError as error:
            logger.error(f"Tasks API error: {error}")
            return False
    
    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 50,
        **kwargs
    ) -> ConnectorResult:
        """
        Fetch tasks from Google Tasks API.

        Args:
            since: Fetch tasks updated after this timestamp
            limit: Maximum number of tasks to fetch (applied per tasklist then globally)
            **kwargs: Additional parameters
                - include_completed: Include completed tasks (default: False)
                - include_hidden: Include hidden/deleted tasks (default: False)
                - due_min: Only fetch tasks due after this date
                - due_max: Only fetch tasks due before this date
                - tasklist_ids: List of specific tasklist IDs to fetch from (default: all)

        Returns:
            ConnectorResult with normalized task data
        """
        if not self.is_connected():
            connected = await self.connect()
            if not connected:
                return ConnectorResult(
                    source=self.source_name,
                    items=[],
                    status="error",
                    error_message="Failed to connect to Tasks API",
                    fetched_at=datetime.now(timezone.utc),
                    since_timestamp=since,
                )

        try:
            all_tasks = []

            # Get task lists (either all or specified ones)
            tasklist_ids = kwargs.get('tasklist_ids')
            if tasklist_ids:
                # Fetch specific tasklists
                tasklists = []
                for tasklist_id in tasklist_ids:
                    try:
                        tasklist = self._service.tasklists().get(tasklist=tasklist_id).execute()
                        tasklists.append(tasklist)
                    except HttpError as e:
                        logger.warning(f"Could not fetch tasklist {tasklist_id}: {e}")
                        continue
            else:
                # Get all tasklists
                tasklists_result = self._service.tasklists().list().execute()
                tasklists = tasklists_result.get('items', [])

            # Fetch tasks from each tasklist
            for tasklist in tasklists:
                tasklist_id = tasklist['id']
                tasklist_title = tasklist['title']

                # Build API parameters according to Google Tasks API reference
                params = {
                    'tasklist': tasklist_id,
                    'maxResults': min(limit, 100),  # API limit is 100 per request
                }

                # Filter by update time (updatedMin parameter)
                if since:
                    params['updatedMin'] = since.isoformat() + 'Z'  # RFC 3339 format

                # Task visibility filters
                include_completed = kwargs.get('include_completed', False)
                include_hidden = kwargs.get('include_hidden', False)

                params['showCompleted'] = include_completed
                params['showHidden'] = include_hidden
                params['showDeleted'] = include_hidden  # Include deleted tasks if hidden requested

                # Due date filters
                if 'due_min' in kwargs:
                    params['dueMin'] = kwargs['due_min'].isoformat() + 'Z'
                if 'due_max' in kwargs:
                    params['dueMax'] = kwargs['due_max'].isoformat() + 'Z'

                # Handle pagination (Google Tasks API supports pageToken)
                page_token = None
                tasklist_tasks = []

                while len(tasklist_tasks) < limit:
                    if page_token:
                        params['pageToken'] = page_token

                    try:
                        tasks_result = self._service.tasks().list(**params).execute()
                    except HttpError as e:
                        logger.warning(f"Error fetching tasks from list '{tasklist_title}': {e}")
                        break

                    tasks = tasks_result.get('items', [])
                    tasklist_tasks.extend(tasks)

                    # Check for next page
                    page_token = tasks_result.get('nextPageToken')
                    if not page_token:
                        break

                    # Remove pageToken for next iteration
                    params.pop('pageToken', None)

                # Normalize tasks from this list
                for task in tasklist_tasks[:limit]:  # Limit per tasklist
                    normalized = self._normalize_task(task, tasklist_title)
                    if normalized:
                        all_tasks.append(normalized)

            # Sort by priority: overdue, due today, due soon, then by due date
            def sort_key(task):
                if task.get('is_overdue'):
                    return (0, task.get('due_date') or '9999-12-31')
                elif task.get('is_due_today'):
                    return (1, task.get('due_date') or '9999-12-31')
                elif task.get('is_due_soon'):
                    return (2, task.get('due_date') or '9999-12-31')
                else:
                    return (3, task.get('due_date') or '9999-12-31')

            all_tasks.sort(key=sort_key)

            return ConnectorResult(
                source=self.source_name,
                items=all_tasks[:limit],  # Final global limit
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
    
    def _normalize_task(self, task: Dict[str, Any], list_name: str) -> Optional[Dict[str, Any]]:
        """
        Normalize Google Tasks API task to standard format.

        Based on Google Tasks API v1 task resource:
        https://developers.google.com/workspace/tasks/reference/rest/v1/tasks

        Returns:
            Normalized task dict or None if parsing fails
        """
        try:
            # Parse timestamps (RFC 3339 format from API)
            updated_str = task.get('updated')
            if updated_str:
                # Remove 'Z' and add UTC offset for parsing
                updated_dt = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
            else:
                updated_dt = datetime.now(timezone.utc)

            # Parse due date (optional, RFC 3339 format)
            due_date = None
            due_datetime = None
            due_date_str = task.get('due')
            if due_date_str:
                # API returns full RFC 3339 datetime, but we often just want the date
                due_datetime = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                due_date = due_datetime.date().isoformat()  # YYYY-MM-DD format

            # Parse completed date (optional, RFC 3339 format)
            completed_date = None
            completed_str = task.get('completed')
            if completed_str:
                completed_dt = datetime.fromisoformat(completed_str.replace('Z', '+00:00'))
                completed_date = completed_dt.isoformat()

            # Calculate time-based metadata
            now = datetime.now(timezone.utc)
            days_until_due = None
            is_overdue = False
            is_due_today = False
            is_due_soon = False

            if due_datetime:
                days_until_due = (due_datetime - now).days
                is_overdue = days_until_due < 0
                is_due_today = days_until_due == 0
                is_due_soon = 0 < days_until_due <= 7

            # Task status interpretation
            status = task.get('status', 'needsAction')
            is_completed = status == 'completed'

            # Extract additional metadata from Google Tasks API
            position = task.get('position')  # String representing task position
            parent_id = task.get('parent')   # Parent task ID for subtasks
            links = task.get('links', [])    # Web links associated with task

            # Build priority assessment
            priority = "normal"
            if is_overdue:
                priority = "urgent"
            elif is_due_today:
                priority = "high"
            elif is_due_soon:
                priority = "medium"

            return {
                "source_id": task['id'],
                "type": "task",
                "timestamp_utc": updated_dt.isoformat(),
                "title": task.get('title', '(No title)'),
                "description": task.get('notes', ''),  # Google Tasks uses 'notes' field
                "list_name": list_name,
                "list_id": task.get('tasklist_id'),  # Will be set by caller

                # Status information
                "status": status,  # needsAction, completed
                "is_completed": is_completed,

                # Due date information
                "due_date": due_date,
                "due_datetime": due_datetime.isoformat() if due_datetime else None,
                "days_until_due": days_until_due,
                "is_overdue": is_overdue,
                "is_due_today": is_due_today,
                "is_due_soon": is_due_soon,

                # Completion information
                "completed_date": completed_date,
                "completed_datetime": completed_str,

                # Task hierarchy and organization
                "parent_task_id": parent_id,
                "position": position,
                "has_subtasks": bool(parent_id),  # Simple indicator

                # Priority assessment
                "priority": priority,

                # Links and metadata
                "url": task.get('selfLink'),
                "web_links": links,

                # Additional Google Tasks API fields
                "etag": task.get('etag'),
                "hidden": task.get('hidden', False),
                "deleted": task.get('deleted', False),

                # Timestamps
                "created_at": task.get('created'),  # Not always available in list response
                "updated_at": updated_dt.isoformat(),
            }
        except Exception as e:
            logger.warning(f"Error normalizing task '{task.get('title', 'unknown')}': {e}")
            return None

    async def get_tasklists(self) -> List[Dict[str, Any]]:
        """
        Get all user's tasklists.

        Based on Google Tasks API: GET /tasks/v1/users/@me/lists

        Returns:
            List of tasklist dictionaries with id, title, updated, etc.
        """
        if not self.is_connected():
            connected = await self.connect()
            if not connected:
                logger.error("Cannot get tasklists: not connected to Tasks API")
                return []

        try:
            result = self._service.tasklists().list().execute()
            tasklists = result.get('items', [])

            # Normalize tasklist data
            normalized_lists = []
            for tasklist in tasklists:
                normalized_lists.append({
                    "id": tasklist['id'],
                    "title": tasklist['title'],
                    "updated": tasklist.get('updated'),
                    "url": tasklist.get('selfLink'),
                })

            return normalized_lists
        except HttpError as error:
            logger.error(f"Error fetching tasklists: {error}")
            return []

    async def clear_completed_tasks(self, tasklist_id: Optional[str] = None) -> bool:
        """
        Clear all completed tasks from specified tasklist or default tasklist.

        Based on Google Tasks API: POST /tasks/v1/lists/{tasklist}/clear

        Args:
            tasklist_id: ID of tasklist to clear (default: '@default')

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            connected = await self.connect()
            if not connected:
                logger.error("Cannot clear tasks: not connected to Tasks API")
                return False

        try:
            target_list = tasklist_id or '@default'
            self._service.tasks().clear(tasklist=target_list).execute()
            logger.info(f"Cleared completed tasks from tasklist: {target_list}")
            return True
        except HttpError as error:
            logger.error(f"Error clearing completed tasks: {error}")
            return False
