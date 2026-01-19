"""
Google Tasks MCP Connector
Fetches tasks via Google Tasks API
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
    
    @property
    def source_name(self) -> str:
        return "tasks"
    
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
        Fetch tasks.
        
        Args:
            since: Fetch tasks updated after this timestamp
            limit: Maximum number of tasks to fetch
            **kwargs: Additional parameters
                - include_completed: Include completed tasks (default: False)
                - due_max: Only fetch tasks due before this date
        
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
                    error_message="Failed to connect to Tasks",
                    fetched_at=datetime.now(timezone.utc),
                    since_timestamp=since,
                )
        
        try:
            all_tasks = []
            
            # Get all task lists
            tasklists = self._service.tasklists().list().execute()
            
            for tasklist in tasklists.get('items', []):
                tasklist_id = tasklist['id']
                tasklist_title = tasklist['title']
                
                # Fetch tasks from this list
                params = {
                    'tasklist': tasklist_id,
                    'maxResults': limit,
                }
                
                # Filter by update time if provided
                if since:
                    params['updatedMin'] = since.isoformat()
                
                # Include or exclude completed tasks
                if not kwargs.get('include_completed', False):
                    params['showCompleted'] = False
                    params['showHidden'] = False
                
                # Filter by due date if provided
                if 'due_max' in kwargs:
                    params['dueMax'] = kwargs['due_max'].isoformat()
                
                tasks_result = self._service.tasks().list(**params).execute()
                
                tasks = tasks_result.get('items', [])
                
                # Normalize tasks
                for task in tasks:
                    normalized = self._normalize_task(task, tasklist_title)
                    if normalized:
                        all_tasks.append(normalized)
            
            # Sort by due date (tasks without due date go to end)
            all_tasks.sort(key=lambda t: t.get('due_date') or '9999-12-31')
            
            return ConnectorResult(
                source=self.source_name,
                items=all_tasks[:limit],  # Apply limit after collecting from all lists
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
        Normalize Task to standard format.
        
        Returns:
            Normalized task dict or None if parsing fails
        """
        try:
            # Parse update time
            updated = task.get('updated')
            if updated:
                updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            else:
                updated_dt = datetime.now(timezone.utc)
            
            # Parse due date (optional)
            due_date = None
            due_date_str = task.get('due')
            if due_date_str:
                # Due dates are in RFC 3339 format
                due_date = due_date_str[:10]  # Extract YYYY-MM-DD
            
            # Calculate days until due
            days_until_due = None
            if due_date:
                due_dt = datetime.fromisoformat(due_date + 'T00:00:00+00:00')
                now = datetime.now(timezone.utc)
                days_until_due = (due_dt - now).days
            
            return {
                "source_id": task['id'],
                "type": "task",
                "timestamp_utc": updated_dt.isoformat(),
                "title": task.get('title', '(No title)'),
                "notes": task.get('notes', ''),
                "list_name": list_name,
                "status": task.get('status'),  # needsAction, completed
                "is_completed": task.get('status') == 'completed',
                "due_date": due_date,
                "days_until_due": days_until_due,
                "is_overdue": days_until_due < 0 if days_until_due is not None else False,
                "is_due_today": days_until_due == 0 if days_until_due is not None else False,
                "is_due_soon": 0 < days_until_due <= 7 if days_until_due is not None else False,
                "completed_date": task.get('completed'),
                "parent_task_id": task.get('parent'),
                "position": task.get('position'),
                "url": task.get('selfLink'),
                "updated_at": updated_dt.isoformat(),
            }
        except Exception as e:
            logger.warning(f"Error normalizing task: {e}")
            return None
