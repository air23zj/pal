"""
Comprehensive tests for connectors (gmail, calendar, tasks)
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import base64

from packages.connectors.gmail import GmailConnector
from packages.connectors.calendar import CalendarConnector
from packages.connectors.tasks import TasksConnector
from packages.connectors.base import ConnectorResult


class TestGmailConnector:
    """Test GmailConnector"""

    def test_source_name(self):
        """Test source name property"""
        connector = GmailConnector()
        assert connector.source_name == "gmail"

    def test_is_connected_false_initially(self):
        """Test connector is not connected initially"""
        connector = GmailConnector()
        assert connector.is_connected() is False

    @pytest.mark.asyncio
    async def test_connect_no_credentials(self):
        """Test connect fails without credentials"""
        with patch('os.path.exists', return_value=False):
            connector = GmailConnector()
            result = await connector.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.gmail.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = True
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.gmail.build') as mock_build:
                    mock_service = Mock()
                    mock_service.users.return_value.getProfile.return_value.execute.return_value = {}
                    mock_build.return_value = mock_service

                    connector = GmailConnector()
                    result = await connector.connect()

                    assert result is True

    @pytest.mark.asyncio
    async def test_fetch_not_connected(self):
        """Test fetch when not connected returns error"""
        with patch.object(GmailConnector, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = False

            connector = GmailConnector()
            result = await connector.fetch()

            assert result.status == "error"
            assert "Failed to connect" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful fetch"""
        connector = GmailConnector()
        connector._service = Mock()
        connector._connected = True

        # Mock the list call
        mock_list = Mock()
        mock_list.execute.return_value = {
            "messages": [{"id": "msg1"}]
        }
        connector._service.users.return_value.messages.return_value.list.return_value = mock_list

        # Mock the get call
        mock_get = Mock()
        mock_get.execute.return_value = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test email",
            "internalDate": "1705000000000",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "Test Subject"}
                ],
                "body": {"data": base64.urlsafe_b64encode(b"Test body").decode()}
            },
            "labelIds": ["INBOX", "UNREAD"]
        }
        connector._service.users.return_value.messages.return_value.get.return_value = mock_get

        result = await connector.fetch(limit=10)

        assert result.status == "ok"
        assert len(result.items) == 1
        assert result.items[0]["subject"] == "Test Subject"

    @pytest.mark.asyncio
    async def test_fetch_with_since(self):
        """Test fetch with since parameter"""
        connector = GmailConnector()
        connector._service = Mock()
        connector._connected = True

        mock_list = Mock()
        mock_list.execute.return_value = {"messages": []}
        connector._service.users.return_value.messages.return_value.list.return_value = mock_list

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await connector.fetch(since=since)

        # Verify query includes 'after:' timestamp
        call_args = connector._service.users.return_value.messages.return_value.list.call_args
        assert "after:" in call_args.kwargs.get('q', '')

    def test_normalize_message_basic(self):
        """Test message normalization"""
        connector = GmailConnector()
        message = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test snippet",
            "internalDate": "1705000000000",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "Test Subject"}
                ],
                "body": {"data": base64.urlsafe_b64encode(b"Test body").decode()}
            },
            "labelIds": ["INBOX", "UNREAD", "IMPORTANT"]
        }

        result = connector._normalize_message(message)

        assert result is not None
        assert result["source_id"] == "msg1"
        assert result["from"] == "sender@example.com"
        assert result["subject"] == "Test Subject"
        assert result["is_unread"] is True
        assert result["is_important"] is True

    def test_normalize_message_multipart(self):
        """Test normalizing multipart message"""
        connector = GmailConnector()
        message = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test",
            "internalDate": "1705000000000",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test"}
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": base64.urlsafe_b64encode(b"Plain text body").decode()}
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": base64.urlsafe_b64encode(b"<html>HTML body</html>").decode()}
                    }
                ]
            },
            "labelIds": []
        }

        result = connector._normalize_message(message)

        assert result is not None
        assert "Plain text body" in result["body"]

    def test_normalize_message_no_subject(self):
        """Test normalizing message without subject"""
        connector = GmailConnector()
        message = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test",
            "internalDate": "1705000000000",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"}
                ],
                "body": {}
            },
            "labelIds": []
        }

        result = connector._normalize_message(message)

        assert result is not None
        assert result["subject"] == "(No subject)"

    @pytest.mark.asyncio
    async def test_connect_refresh_success(self):
        """Test successful token refresh"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.gmail.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = False
                mock_cred_instance.expired = True
                mock_cred_instance.refresh_token = "refresh"
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.gmail.Request'), \
                     patch('packages.connectors.gmail.build') as mock_build, \
                     patch('builtins.open', MagicMock()):
                    mock_service = Mock()
                    mock_service.users.return_value.getProfile.return_value.execute.return_value = {}
                    mock_build.return_value = mock_service

                    connector = GmailConnector()
                    result = await connector.connect()
                    assert result is True
                    mock_cred_instance.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_refresh_failure(self):
        """Test token refresh failure results in False if no creds_path"""
        with patch('os.path.exists', side_effect=lambda p: p.endswith('token.json')):
            with patch('packages.connectors.gmail.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = False
                mock_cred_instance.expired = True
                mock_cred_instance.refresh_token = "refresh"
                mock_cred_instance.refresh.side_effect = Exception("Refresh failed")
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                connector = GmailConnector()
                result = await connector.connect()
                assert result is False

    @pytest.mark.asyncio
    async def test_connect_http_error(self):
        """Test HttpError during connection"""
        from googleapiclient.errors import HttpError
        with patch('os.path.exists', return_value=True), \
             patch('packages.connectors.gmail.Credentials'), \
             patch('packages.connectors.gmail.build') as mock_build:
            mock_service = Mock()
            error = HttpError(resp=Mock(status=403), content=b'Forbidden')
            mock_service.users.return_value.getProfile.return_value.execute.side_effect = error
            mock_build.return_value = mock_service

            connector = GmailConnector()
            # Manually set connected status for easier testing of connect logic
            result = await connector.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_fetch_http_error(self):
        """Test HttpError during fetch"""
        from googleapiclient.errors import HttpError
        connector = GmailConnector()
        connector._service = Mock()
        connector._connected = True

        error = HttpError(resp=Mock(status=403), content=b'Forbidden')
        connector._service.users.return_value.messages.return_value.list.return_value.execute.side_effect = error

        result = await connector.fetch()
        assert result.status == "error"
        assert "403" in result.error_message

    def test_normalize_message_exception(self):
        """Test handling of unexpected exceptions during normalization"""
        connector = GmailConnector()
        # Missing payload will trigger Exception
        message = {"id": "msg1"}
        result = connector._normalize_message(message)
        assert result is None

    def test_normalize_message_html_only(self):
        """Test normalizing message with only HTML body"""
        connector = GmailConnector()
        message = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test",
            "internalDate": "1705000000000",
            "payload": {
                "headers": [{"name": "From", "value": "sender@example.com"}],
                "parts": [
                    {
                        "mimeType": "text/html",
                        "body": {"data": base64.urlsafe_b64encode(b"<b>HTML</b>").decode()}
                    }
                ]
            }
        }
        result = connector._normalize_message(message)
        assert result is not None
        assert result["body"] == "HTML"


class TestCalendarConnector:
    """Test CalendarConnector"""

    def test_source_name(self):
        """Test source name property"""
        connector = CalendarConnector()
        assert connector.source_name == "calendar"

    def test_is_connected_false_initially(self):
        """Test connector is not connected initially"""
        connector = CalendarConnector()
        assert connector.is_connected() is False

    @pytest.mark.asyncio
    async def test_connect_no_credentials(self):
        """Test connect fails without credentials"""
        with patch('os.path.exists', return_value=False):
            connector = CalendarConnector()
            result = await connector.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_fetch_not_connected(self):
        """Test fetch when not connected returns error"""
        with patch.object(CalendarConnector, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = False

            connector = CalendarConnector()
            result = await connector.fetch()

            assert result.status == "error"

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful fetch"""
        connector = CalendarConnector()
        connector._service = Mock()
        connector._connected = True

        mock_list = Mock()
        mock_list.execute.return_value = {
            "items": [{
                "id": "event1",
                "summary": "Team Meeting",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "status": "confirmed",
                "attendees": []
            }]
        }
        connector._service.events.return_value.list.return_value = mock_list

        result = await connector.fetch(limit=10)

        assert result.status == "ok"
        assert len(result.items) == 1
        assert result.items[0]["title"] == "Team Meeting"

    def test_normalize_event_datetime(self):
        """Test normalizing event with dateTime"""
        connector = CalendarConnector()
        event = {
            "id": "event1",
            "summary": "Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "status": "confirmed"
        }

        result = connector._normalize_event(event)

        assert result is not None
        assert result["source_id"] == "event1"
        assert result["title"] == "Meeting"
        assert result["duration_minutes"] == 60
        assert result["is_all_day"] is False

    def test_normalize_event_all_day(self):
        """Test normalizing all-day event"""
        connector = CalendarConnector()
        event = {
            "id": "event1",
            "summary": "Holiday",
            "start": {"date": "2024-01-15"},
            "end": {"date": "2024-01-16"},
            "status": "confirmed"
        }

        result = connector._normalize_event(event)

        assert result is not None
        assert result["is_all_day"] is True

    def test_normalize_event_with_attendees(self):
        """Test normalizing event with attendees"""
        connector = CalendarConnector()
        event = {
            "id": "event1",
            "summary": "Team Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "attendees": [
                {"email": "alice@example.com", "responseStatus": "accepted", "displayName": "Alice"},
                {"email": "bob@example.com", "responseStatus": "needsAction"}
            ]
        }

        result = connector._normalize_event(event)

        assert result is not None
        assert result["attendee_count"] == 2
        assert len(result["attendees"]) == 2

    def test_extract_meeting_link_google_meet(self):
        """Test extracting Google Meet link"""
        connector = CalendarConnector()
        description = "Join us at https://meet.google.com/abc-def-ghi for the meeting"

        result = connector._extract_meeting_link(description)

        assert result == "https://meet.google.com/abc-def-ghi"

    def test_extract_meeting_link_zoom(self):
        """Test extracting Zoom link"""
        connector = CalendarConnector()
        description = "Join via https://zoom.us/j/1234567890"

        result = connector._extract_meeting_link(description)

        assert result == "https://zoom.us/j/1234567890"

    def test_extract_meeting_link_none(self):
        """Test no meeting link found"""
        connector = CalendarConnector()
        description = "Regular meeting at office"

        result = connector._extract_meeting_link(description)

        assert result is None

    def test_get_reminder_minutes_default(self):
        """Test default reminder"""
        connector = CalendarConnector()
        reminders = {"useDefault": True}

        result = connector._get_reminder_minutes(reminders)

        assert result == 30

    def test_get_reminder_minutes_override(self):
        """Test custom reminder override"""
        connector = CalendarConnector()
        reminders = {"overrides": [{"method": "popup", "minutes": 15}]}

        result = connector._get_reminder_minutes(reminders)

        assert result == 15

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.calendar.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = True
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.calendar.build') as mock_build:
                    mock_service = Mock()
                    mock_service.calendarList.return_value.list.return_value.execute.return_value = {}
                    mock_build.return_value = mock_service

                    connector = CalendarConnector()
                    result = await connector.connect()
                    assert result is True

    @pytest.mark.asyncio
    async def test_connect_refresh_success(self):
        """Test token refresh"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.calendar.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = False
                mock_cred_instance.expired = True
                mock_cred_instance.refresh_token = "refresh"
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.calendar.Request'), \
                     patch('packages.connectors.calendar.build') as mock_build, \
                     patch('builtins.open', MagicMock()):
                    mock_service = Mock()
                    mock_service.calendarList.return_value.list.return_value.execute.return_value = {}
                    mock_build.return_value = mock_service

                    connector = CalendarConnector()
                    result = await connector.connect()
                    assert result is True
                    mock_cred_instance.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_http_error(self):
        """Test HttpError during calendar fetch"""
        from googleapiclient.errors import HttpError
        connector = CalendarConnector()
        connector._service = Mock()
        connector._connected = True

        error = HttpError(resp=Mock(status=403), content=b'Forbidden')
        connector._service.events.return_value.list.return_value.execute.side_effect = error

        result = await connector.fetch()
        assert result.status == "error"

    def test_normalize_event_exception(self):
        """Test event normalization error handling"""
        connector = CalendarConnector()
        # Invalid event missing 'start'
        result = connector._normalize_event({"id": "ev1"})
        assert result is None

    def test_extract_meeting_link_teams(self):
        """Test extracting Teams link"""
        connector = CalendarConnector()
        desc = "Join at https://teams.microsoft.com/l/meetup-join/xyz"
        assert connector._extract_meeting_link(desc) == "https://teams.microsoft.com/l/meetup-join/xyz"

    def test_get_reminder_minutes_none_explicit(self):
        """Test explicit none reminder"""
        connector = CalendarConnector()
        assert connector._get_reminder_minutes({}) is None


class TestTasksConnector:
    """Test TasksConnector"""

    def test_source_name(self):
        """Test source name property"""
        connector = TasksConnector()
        assert connector.source_name == "tasks"

    def test_is_connected_false_initially(self):
        """Test connector is not connected initially"""
        connector = TasksConnector()
        assert connector.is_connected() is False

    @pytest.mark.asyncio
    async def test_connect_no_credentials(self):
        """Test connect fails without credentials"""
        with patch('os.path.exists', return_value=False):
            connector = TasksConnector()
            result = await connector.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_fetch_not_connected(self):
        """Test fetch when not connected returns error"""
        with patch.object(TasksConnector, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = False

            connector = TasksConnector()
            result = await connector.fetch()

            assert result.status == "error"

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful fetch"""
        connector = TasksConnector()
        connector._service = Mock()
        connector._connected = True

        # Mock tasklists
        mock_tasklists = Mock()
        mock_tasklists.execute.return_value = {
            "items": [{"id": "list1", "title": "My Tasks"}]
        }
        connector._service.tasklists.return_value.list.return_value = mock_tasklists

        # Mock tasks
        mock_tasks = Mock()
        mock_tasks.execute.return_value = {
            "items": [{
                "id": "task1",
                "title": "Complete report",
                "status": "needsAction",
                "updated": "2024-01-15T10:00:00Z"
            }]
        }
        connector._service.tasks.return_value.list.return_value = mock_tasks

        result = await connector.fetch(limit=10)

        assert result.status == "ok"
        assert len(result.items) == 1
        assert result.items[0]["title"] == "Complete report"

    @pytest.mark.asyncio
    async def test_fetch_with_options(self):
        """Test fetch with options"""
        connector = TasksConnector()
        connector._service = Mock()
        connector._connected = True

        mock_tasklists = Mock()
        mock_tasklists.execute.return_value = {"items": [{"id": "list1", "title": "Tasks"}]}
        connector._service.tasklists.return_value.list.return_value = mock_tasklists

        mock_tasks = Mock()
        mock_tasks.execute.return_value = {"items": []}
        connector._service.tasks.return_value.list.return_value = mock_tasks

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await connector.fetch(
            since=since,
            include_completed=True,
            due_max=datetime.now(timezone.utc) + timedelta(days=7)
        )

        assert result.status == "ok"

    def test_normalize_task_basic(self):
        """Test basic task normalization"""
        connector = TasksConnector()
        task = {
            "id": "task1",
            "title": "Complete report",
            "status": "needsAction",
            "updated": "2024-01-15T10:00:00Z"
        }

        result = connector._normalize_task(task, "My Tasks")

        assert result is not None
        assert result["source_id"] == "task1"
        assert result["title"] == "Complete report"
        assert result["is_completed"] is False
        assert result["list_name"] == "My Tasks"

    def test_normalize_task_with_due_date(self):
        """Test task normalization with due date"""
        connector = TasksConnector()
        # Set due date to 3 days from now (clearly "due soon")
        future_date = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT00:00:00.000Z")
        task = {
            "id": "task1",
            "title": "Urgent task",
            "status": "needsAction",
            "updated": "2024-01-15T10:00:00Z",
            "due": future_date
        }

        result = connector._normalize_task(task, "Tasks")

        assert result is not None
        assert result["due_date"] is not None
        # Days until due should be around 2-3 (depending on time of day)
        assert result["days_until_due"] >= 2
        assert result["is_overdue"] is False

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.tasks.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = True
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.tasks.build') as mock_build:
                    mock_service = Mock()
                    # Tasks connector connect just builds the service
                    mock_build.return_value = mock_service

                    connector = TasksConnector()
                    result = await connector.connect()
                    assert result is True

    @pytest.mark.asyncio
    async def test_connect_refresh_success(self):
        """Test token refresh"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.tasks.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = False
                mock_cred_instance.expired = True
                mock_cred_instance.refresh_token = "refresh"
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.tasks.Request'), \
                     patch('packages.connectors.tasks.build') as mock_build, \
                     patch('builtins.open', MagicMock()):
                    mock_service = Mock()
                    mock_build.return_value = mock_service

                    connector = TasksConnector()
                    result = await connector.connect()
                    assert result is True
                    mock_cred_instance.refresh.assert_called_once()

    def test_normalize_task_overdue(self):
        """Test normalizing overdue task"""
        connector = TasksConnector()
        # Set due date to yesterday
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z")
        task = {
            "id": "task1",
            "title": "Late task",
            "status": "needsAction",
            "updated": "2024-01-15T10:00:00Z",
            "due": yesterday
        }

        result = connector._normalize_task(task, "Tasks")

        assert result is not None
        assert result["is_overdue"] is True

    def test_normalize_task_completed(self):
        """Test normalizing completed task"""
        connector = TasksConnector()
        task = {
            "id": "task1",
            "title": "Done task",
            "status": "completed",
            "updated": "2024-01-15T10:00:00Z",
            "completed": "2024-01-15T11:00:00Z"
        }

        result = connector._normalize_task(task, "Tasks")

        assert result is not None
        assert result["is_completed"] is True
        assert result["completed_date"] is not None

    def test_normalize_task_with_notes(self):
        """Test normalizing task with notes"""
        connector = TasksConnector()
        task = {
            "id": "task1",
            "title": "Task with notes",
            "status": "needsAction",
            "updated": "2024-01-15T10:00:00Z",
            "notes": "Some additional details"
        }

        result = connector._normalize_task(task, "Tasks")

        assert result is not None
        assert result["notes"] == "Some additional details"

    @pytest.mark.asyncio
    async def test_fetch_http_error(self):
        """Test HttpError during tasks fetch"""
        from googleapiclient.errors import HttpError
        connector = TasksConnector()
        connector._service = Mock()
        connector._connected = True

        error = HttpError(resp=Mock(status=403), content=b'Forbidden')
        connector._service.tasklists.return_value.list.return_value.execute.side_effect = error

        result = await connector.fetch()
        assert result.status == "error"

    def test_normalize_task_exception(self):
        """Test task normalization error handling"""
        connector = TasksConnector()
        # Missing 'id'
        result = connector._normalize_task({}, "List")
        assert result is None


class TestConnectorResult:
    """Test ConnectorResult"""

    def test_connector_result_creation(self):
        """Test creating ConnectorResult"""
        result = ConnectorResult(
            source="gmail",
            items=[{"id": "1"}],
            status="ok",
            fetched_at=datetime.now(timezone.utc)
        )

        assert result.source == "gmail"
        assert result.status == "ok"
        assert len(result.items) == 1

    def test_connector_result_with_error(self):
        """Test creating ConnectorResult with error"""
        result = ConnectorResult(
            source="gmail",
            items=[],
            status="error",
            error_message="Connection failed",
            fetched_at=datetime.now(timezone.utc)
        )

        assert result.status == "error"
        assert result.error_message == "Connection failed"

    def test_connector_result_with_since(self):
        """Test ConnectorResult with since timestamp"""
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = ConnectorResult(
            source="calendar",
            items=[],
            status="ok",
            fetched_at=datetime.now(timezone.utc),
            since_timestamp=since
        )

        assert result.since_timestamp == since


class TestConnectorIntegration:
    """Integration tests for connectors"""

    @pytest.mark.asyncio
    async def test_gmail_connector_full_flow(self):
        """Test Gmail connector full flow"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.gmail.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = True
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.gmail.build') as mock_build:
                    mock_service = Mock()
                    mock_service.users.return_value.getProfile.return_value.execute.return_value = {}
                    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
                        "messages": []
                    }
                    mock_build.return_value = mock_service

                    connector = GmailConnector()
                    await connector.connect()
                    result = await connector.fetch()

                    assert result.status == "ok"

    @pytest.mark.asyncio
    async def test_calendar_connector_full_flow(self):
        """Test Calendar connector full flow"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.calendar.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = True
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.calendar.build') as mock_build:
                    mock_service = Mock()
                    mock_service.calendarList.return_value.list.return_value.execute.return_value = {}
                    mock_service.events.return_value.list.return_value.execute.return_value = {
                        "items": []
                    }
                    mock_build.return_value = mock_service

                    connector = CalendarConnector()
                    await connector.connect()
                    result = await connector.fetch()

                    assert result.status == "ok"

    @pytest.mark.asyncio
    async def test_tasks_connector_full_flow(self):
        """Test Tasks connector full flow"""
        with patch('os.path.exists', return_value=True):
            with patch('packages.connectors.tasks.Credentials') as mock_creds:
                mock_cred_instance = Mock()
                mock_cred_instance.valid = True
                mock_creds.from_authorized_user_file.return_value = mock_cred_instance

                with patch('packages.connectors.tasks.build') as mock_build:
                    mock_service = Mock()
                    mock_service.tasklists.return_value.list.return_value.execute.return_value = {
                        "items": []
                    }
                    mock_build.return_value = mock_service

                    connector = TasksConnector()
                    await connector.connect()
                    result = await connector.fetch()

                    assert result.status == "ok"
