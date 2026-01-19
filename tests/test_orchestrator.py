"""
Comprehensive tests for orchestrator module - Target 80%+ coverage
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio

from packages.orchestrator.orchestrator import (
    BriefOrchestrator,
    BriefStatus,
    run_brief_generation,
)
from packages.shared.schemas import (
    BriefItem, BriefBundle, ModuleResult, NoveltyInfo, RankingScores, Entity
)


def create_test_item(
    item_ref: str = "test_item",
    source: str = "gmail",
    item_type: str = "email",
    novelty_label: str = "NEW"
) -> BriefItem:
    """Helper to create test items"""
    timestamp = datetime.now(timezone.utc).isoformat()
    return BriefItem(
        item_ref=item_ref,
        source=source,
        type=item_type,
        timestamp_utc=timestamp,
        title=f"Test {item_ref}",
        summary=f"Summary for {item_ref}",
        why_it_matters="Test",
        entities=[],
        novelty=NoveltyInfo(
            label=novelty_label,
            reason="Test",
            first_seen_utc=timestamp
        ),
        ranking=RankingScores(
            relevance_score=0.5,
            urgency_score=0.5,
            credibility_score=0.5,
            impact_score=0.5,
            actionability_score=0.5,
            final_score=0.5
        ),
        evidence=[],
        suggested_actions=[]
    )


class TestBriefStatus:
    """Test BriefStatus enum"""

    def test_status_values(self):
        """Test status enum values"""
        assert BriefStatus.QUEUED == "queued"
        assert BriefStatus.RUNNING == "running"
        assert BriefStatus.SUCCESS == "ok"
        assert BriefStatus.DEGRADED == "degraded"
        assert BriefStatus.ERROR == "error"

    def test_status_is_string(self):
        """Test status is string enum"""
        assert isinstance(BriefStatus.SUCCESS.value, str)


class TestBriefOrchestratorInit:
    """Test BriefOrchestrator initialization"""

    def test_init_basic(self):
        """Test basic initialization"""
        orchestrator = BriefOrchestrator(user_id="user123")
        assert orchestrator.user_id == "user123"
        assert orchestrator.user_preferences == {}
        assert orchestrator.progress_callback is None
        assert orchestrator.warnings == []
        assert orchestrator.errors == []

    def test_init_with_preferences(self):
        """Test initialization with preferences"""
        prefs = {"topics": ["AI"], "timezone": "America/New_York"}
        orchestrator = BriefOrchestrator(
            user_id="user123",
            user_preferences=prefs
        )
        assert orchestrator.user_preferences == prefs

    def test_init_with_callback(self):
        """Test initialization with progress callback"""
        callback = Mock()
        orchestrator = BriefOrchestrator(
            user_id="user123",
            progress_callback=callback
        )
        assert orchestrator.progress_callback == callback

    def test_init_creates_components(self):
        """Test that components are initialized"""
        orchestrator = BriefOrchestrator(user_id="user123")
        assert orchestrator.memory_manager is not None
        assert orchestrator.novelty_detector is not None
        assert orchestrator.ranker is not None


class TestReportProgress:
    """Test progress reporting"""

    def test_report_progress_with_callback(self):
        """Test progress is reported to callback"""
        callback = Mock()
        orchestrator = BriefOrchestrator(
            user_id="user123",
            progress_callback=callback
        )
        orchestrator._report_progress("test_stage", 0.5, "Test message")
        callback.assert_called_once_with("test_stage", 0.5, "Test message")

    def test_report_progress_no_callback(self):
        """Test progress without callback doesn't raise"""
        orchestrator = BriefOrchestrator(user_id="user123")
        # Should not raise
        orchestrator._report_progress("test_stage", 0.5, "Test message")

    def test_report_progress_callback_error_handled(self):
        """Test callback errors are handled gracefully"""
        callback = Mock(side_effect=Exception("Callback error"))
        orchestrator = BriefOrchestrator(
            user_id="user123",
            progress_callback=callback
        )
        # Should not raise, error is caught
        orchestrator._report_progress("test_stage", 0.5, "Test message")


class TestNormalizeAllData:
    """Test data normalization"""

    def test_normalize_empty_data(self):
        """Test normalizing empty data"""
        orchestrator = BriefOrchestrator(user_id="user123")
        result = orchestrator._normalize_all_data({})
        assert result == []

    def test_normalize_gmail_data(self):
        """Test normalizing Gmail data"""
        orchestrator = BriefOrchestrator(user_id="user123")
        # Use normalized connector format (what connectors output after _normalize_message)
        raw_data = {
            "gmail": [{
                "source_id": "msg123",
                "type": "email",
                "timestamp_utc": "2024-01-15T10:00:00+00:00",
                "from": "sender@example.com",
                "subject": "Test Subject",
                "snippet": "Test email content",
                "body": "Email body",
                "labels": ["INBOX"],
                "thread_id": "thread123",
                "is_unread": True,
                "is_important": False,
                "url": "https://mail.google.com/mail/u/0/#inbox/msg123"
            }]
        }
        result = orchestrator._normalize_all_data(raw_data)
        assert len(result) == 1
        assert result[0].source == "gmail"

    def test_normalize_calendar_data(self):
        """Test normalizing Calendar data"""
        orchestrator = BriefOrchestrator(user_id="user123")
        # Use normalized connector format
        raw_data = {
            "calendar": [{
                "source_id": "event123",
                "type": "event",
                "timestamp_utc": "2024-01-15T10:00:00+00:00",
                "title": "Meeting",
                "description": "Test meeting",
                "location": "Office",
                "start_time": "2024-01-15T10:00:00+00:00",
                "end_time": "2024-01-15T11:00:00+00:00",
                "duration_minutes": 60,
                "is_all_day": False,
                "attendees": [],
                "attendee_count": 0,
                "organizer": "organizer@example.com",
                "status": "confirmed",
                "url": "https://calendar.google.com/event?eid=event123"
            }]
        }
        result = orchestrator._normalize_all_data(raw_data)
        assert len(result) == 1
        assert result[0].source == "calendar"

    def test_normalize_tasks_data(self):
        """Test normalizing Tasks data"""
        orchestrator = BriefOrchestrator(user_id="user123")
        # Use normalized connector format
        raw_data = {
            "tasks": [{
                "source_id": "task123",
                "type": "task",
                "timestamp_utc": "2024-01-15T10:00:00+00:00",
                "title": "Complete report",
                "notes": "",
                "list_name": "My Tasks",
                "status": "needsAction",
                "is_completed": False,
                "due_date": None,
                "days_until_due": None,
                "is_overdue": False,
                "is_due_today": False,
                "is_due_soon": False
            }]
        }
        result = orchestrator._normalize_all_data(raw_data)
        assert len(result) == 1
        assert result[0].source == "tasks"

    def test_normalize_social_data(self):
        """Test normalizing social media data"""
        orchestrator = BriefOrchestrator(user_id="user123")
        raw_data = {
            "twitter": [{
                "id": "post123",
                "author": "user1",
                "content": "Hello world",
                "timestamp": "2024-01-15T12:00:00Z"
            }]
        }
        result = orchestrator._normalize_all_data(raw_data)
        assert len(result) == 1
        assert result[0].source == "twitter"

    def test_normalize_handles_errors(self):
        """Test normalization handles errors gracefully"""
        orchestrator = BriefOrchestrator(user_id="user123")
        # Invalid data that will cause normalization to fail
        raw_data = {
            "gmail": [{"invalid": "data"}]
        }
        # Should not raise, errors are collected
        result = orchestrator._normalize_all_data(raw_data)
        # May be empty or have partial results
        assert isinstance(result, list)

    def test_normalize_skips_empty_sources(self):
        """Test normalization skips empty sources"""
        orchestrator = BriefOrchestrator(user_id="user123")
        raw_data = {
            "gmail": [],
            "calendar": None,
            "tasks": []
        }
        result = orchestrator._normalize_all_data(raw_data)
        assert result == []


class TestOrganizeByModule:
    """Test organizing items by module"""

    def test_organize_basic(self):
        """Test basic organization by module"""
        orchestrator = BriefOrchestrator(user_id="user123")
        items = [
            create_test_item("item1", source="gmail"),
            create_test_item("item2", source="gmail"),
            create_test_item("item3", source="calendar"),
        ]
        module_results, highlights = orchestrator._organize_by_module(items)

        assert "gmail" in module_results
        assert "calendar" in module_results
        assert len(module_results["gmail"].items) == 2
        assert len(module_results["calendar"].items) == 1

    def test_organize_caps_items_per_module(self):
        """Test that items are capped at 8 per module"""
        orchestrator = BriefOrchestrator(user_id="user123")
        items = [create_test_item(f"item{i}", source="gmail") for i in range(15)]
        module_results, _ = orchestrator._organize_by_module(items)

        assert len(module_results["gmail"].items) == 8

    def test_organize_counts_novelty(self):
        """Test that novelty counts are calculated"""
        orchestrator = BriefOrchestrator(user_id="user123")
        items = [
            create_test_item("item1", source="gmail", novelty_label="NEW"),
            create_test_item("item2", source="gmail", novelty_label="NEW"),
            create_test_item("item3", source="gmail", novelty_label="UPDATED"),
            create_test_item("item4", source="gmail", novelty_label="REPEAT"),
        ]
        module_results, _ = orchestrator._organize_by_module(items)

        assert module_results["gmail"].new_count == 2
        assert module_results["gmail"].updated_count == 1

    def test_organize_selects_highlights(self):
        """Test that highlights are selected"""
        orchestrator = BriefOrchestrator(user_id="user123")
        items = [create_test_item(f"item{i}", source="gmail") for i in range(10)]
        _, highlights = orchestrator._organize_by_module(items)

        assert len(highlights) <= 5  # Max 5 highlights

    def test_organize_empty_items(self):
        """Test organizing empty item list"""
        orchestrator = BriefOrchestrator(user_id="user123")
        module_results, highlights = orchestrator._organize_by_module([])

        assert module_results == {}
        assert highlights == []


class TestCreateBriefBundle:
    """Test brief bundle creation"""

    def test_create_bundle_basic(self):
        """Test basic bundle creation"""
        orchestrator = BriefOrchestrator(user_id="user123")
        items = [create_test_item("item1")]
        module_results = {
            "gmail": ModuleResult(
                status="ok",
                summary="1 new",
                new_count=1,
                updated_count=0,
                items=items
            )
        }
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        start_time = datetime.now(timezone.utc)

        bundle = orchestrator._create_brief_bundle(
            final_items=items,
            module_results=module_results,
            module_summaries={},
            top_highlights=items,
            since=since,
            start_time=start_time,
        )

        assert bundle.user_id == "user123"
        assert bundle.brief_id.startswith("brief_")
        assert "gmail" in bundle.modules

    def test_create_bundle_with_errors(self):
        """Test bundle creation with errors sets DEGRADED status"""
        orchestrator = BriefOrchestrator(user_id="user123")
        orchestrator.errors.append("Test error")

        items = [create_test_item("item1")]
        module_results = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items)}

        bundle = orchestrator._create_brief_bundle(
            final_items=items,
            module_results=module_results,
            module_summaries={},
            top_highlights=items,
            since=datetime.now(timezone.utc),
            start_time=datetime.now(timezone.utc),
        )

        assert bundle.run_metadata["status"] == "degraded"

    def test_create_bundle_with_warnings(self):
        """Test bundle creation with warnings sets DEGRADED status"""
        orchestrator = BriefOrchestrator(user_id="user123")
        orchestrator.warnings.append("Test warning")

        items = [create_test_item("item1")]
        module_results = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items)}

        bundle = orchestrator._create_brief_bundle(
            final_items=items,
            module_results=module_results,
            module_summaries={},
            top_highlights=items,
            since=datetime.now(timezone.utc),
            start_time=datetime.now(timezone.utc),
        )

        assert bundle.run_metadata["status"] == "degraded"

    def test_create_bundle_success_status(self):
        """Test bundle creation without errors/warnings sets SUCCESS"""
        orchestrator = BriefOrchestrator(user_id="user123")

        items = [create_test_item("item1")]
        module_results = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items)}

        bundle = orchestrator._create_brief_bundle(
            final_items=items,
            module_results=module_results,
            module_summaries={},
            top_highlights=items,
            since=datetime.now(timezone.utc),
            start_time=datetime.now(timezone.utc),
        )

        assert bundle.run_metadata["status"] == "ok"

    def test_create_bundle_with_user_timezone(self):
        """Test bundle uses user timezone from preferences"""
        orchestrator = BriefOrchestrator(
            user_id="user123",
            user_preferences={"timezone": "America/New_York"}
        )

        items = [create_test_item("item1")]
        module_results = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items)}

        bundle = orchestrator._create_brief_bundle(
            final_items=items,
            module_results=module_results,
            module_summaries={},
            top_highlights=items,
            since=datetime.now(timezone.utc),
            start_time=datetime.now(timezone.utc),
        )

        assert bundle.timezone == "America/New_York"

    def test_create_bundle_with_module_summaries(self):
        """Test bundle creation applies module summaries"""
        orchestrator = BriefOrchestrator(user_id="user123")

        items = [create_test_item("item1")]
        module_results = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items)}
        module_summaries = {"gmail": "You have 1 important email"}

        bundle = orchestrator._create_brief_bundle(
            final_items=items,
            module_results=module_results,
            module_summaries=module_summaries,
            top_highlights=items,
            since=datetime.now(timezone.utc),
            start_time=datetime.now(timezone.utc),
        )

        assert bundle.modules["gmail"].summary == "You have 1 important email"


class TestFetchAllData:
    """Test data fetching"""

    @pytest.mark.asyncio
    async def test_fetch_unknown_module(self):
        """Test fetching from unknown module adds warning"""
        orchestrator = BriefOrchestrator(user_id="user123")
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        result = await orchestrator._fetch_all_data(["unknown_module"], since)

        assert "Unknown module: unknown_module" in orchestrator.warnings

    @pytest.mark.asyncio
    async def test_fetch_twitter_adds_warning(self):
        """Test fetching twitter adds setup warning"""
        orchestrator = BriefOrchestrator(user_id="user123")
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        result = await orchestrator._fetch_all_data(["twitter"], since)

        assert any("Twitter" in w for w in orchestrator.warnings)
        assert result.get("twitter") == []

    @pytest.mark.asyncio
    async def test_fetch_linkedin_adds_warning(self):
        """Test fetching linkedin adds setup warning"""
        orchestrator = BriefOrchestrator(user_id="user123")
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        result = await orchestrator._fetch_all_data(["linkedin"], since)

        assert any("LinkedIn" in w for w in orchestrator.warnings)
        assert result.get("linkedin") == []

    @pytest.mark.asyncio
    async def test_fetch_data_error_handled(self):
        """Test fetch error is caught and reported"""
        orchestrator = BriefOrchestrator(user_id="user123")
        
        with patch('packages.connectors.gmail.GmailConnector.fetch', side_effect=Exception("Fetch failed")):
            result = await orchestrator._fetch_all_data(["gmail"], datetime.now(timezone.utc))
            assert "gmail: Fetch failed" in orchestrator.errors
            assert result["gmail"] == []

    def test_normalize_data_error_handled(self):
        """Test normalization error is caught and reported"""
        orchestrator = BriefOrchestrator(user_id="user123")
        
        with patch('packages.normalizer.normalizer.Normalizer.normalize_gmail_item', side_effect=Exception("Norm failed")):
            result = orchestrator._normalize_all_data({"gmail": [{"id": "1"}]})
            assert any("Normalization error in gmail" in e for e in orchestrator.errors)
            assert result == []


class TestApplyNoveltyDetection:
    """Test novelty detection application"""

    @pytest.mark.asyncio
    async def test_apply_novelty_basic(self):
        """Test basic novelty detection"""
        orchestrator = BriefOrchestrator(user_id="user123")
        items = [create_test_item("item1")]
        raw_data = {"gmail": [{"id": "msg1", "title": "Test"}]}

        result = await orchestrator._apply_novelty_detection(items, raw_data)

        assert len(result) == 1
        assert result[0].novelty is not None

    @pytest.mark.asyncio
    async def test_apply_novelty_empty_raw_data(self):
        """Test novelty detection with empty raw data"""
        orchestrator = BriefOrchestrator(user_id="user123")
        items = [create_test_item("item1")]

        result = await orchestrator._apply_novelty_detection(items, {})

        assert len(result) == 1


class TestSynthesizeBrief:
    """Test LLM synthesis"""

    @pytest.mark.asyncio
    async def test_synthesize_handles_llm_error(self):
        """Test synthesis handles LLM errors gracefully"""
        orchestrator = BriefOrchestrator(user_id="user123")

        # Mock the synthesizer to fail
        with patch('packages.orchestrator.orchestrator.get_llm_client') as mock_llm:
            mock_llm.side_effect = RuntimeError("No LLM available")

            items = [create_test_item("item1")]
            module_results = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items)}

            final_items, summaries = await orchestrator._synthesize_brief(items, module_results)

            # Should return original items and empty summaries on error
            assert len(final_items) == 1
            assert "LLM synthesis failed" in orchestrator.warnings[0]


class TestGenerateBrief:
    """Test full brief generation"""

    @pytest.mark.asyncio
    async def test_generate_brief_with_mocked_connectors(self):
        """Test full brief generation with mocked connectors"""
        with patch('packages.orchestrator.orchestrator.BriefOrchestrator._fetch_all_data') as mock_fetch:
            # Mock fetch to return sample data
            mock_fetch.return_value = {
                "gmail": [{
                    "id": "msg1",
                    "threadId": "thread1",
                    "snippet": "Test email",
                    "internalDate": "1705000000000",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "sender@example.com"},
                            {"name": "Subject", "value": "Test"}
                        ]
                    }
                }]
            }

            with patch('packages.orchestrator.orchestrator.get_llm_client') as mock_llm:
                mock_llm.side_effect = RuntimeError("No LLM")

                orchestrator = BriefOrchestrator(user_id="user123")
                bundle = await orchestrator.generate_brief(modules=["gmail"])

                assert bundle is not None
                assert bundle.user_id == "user123"

    @pytest.mark.asyncio
    async def test_generate_brief_default_modules(self):
        """Test brief generation uses default modules"""
        with patch('packages.orchestrator.orchestrator.BriefOrchestrator._fetch_all_data') as mock_fetch:
            mock_fetch.return_value = {"gmail": [], "calendar": [], "tasks": []}

            with patch('packages.orchestrator.orchestrator.get_llm_client') as mock_llm:
                mock_llm.side_effect = RuntimeError("No LLM")

                orchestrator = BriefOrchestrator(user_id="user123")
                bundle = await orchestrator.generate_brief()

                # Should call with default modules
                mock_fetch.assert_called_once()
                call_args = mock_fetch.call_args
                modules = call_args[0][0]
                assert "gmail" in modules
                assert "calendar" in modules
                assert "tasks" in modules

    @pytest.mark.asyncio
    async def test_generate_brief_default_since(self):
        """Test brief generation uses 24h default for since"""
        with patch('packages.orchestrator.orchestrator.BriefOrchestrator._fetch_all_data') as mock_fetch:
            mock_fetch.return_value = {}

            with patch('packages.orchestrator.orchestrator.get_llm_client') as mock_llm:
                mock_llm.side_effect = RuntimeError("No LLM")

                orchestrator = BriefOrchestrator(user_id="user123")
                bundle = await orchestrator.generate_brief()

                # Since should be approximately 24 hours ago
                call_args = mock_fetch.call_args
                since = call_args[0][1]
                time_diff = datetime.now(timezone.utc) - since
                assert 23 <= time_diff.total_seconds() / 3600 <= 25

    @pytest.mark.asyncio
    async def test_generate_brief_reports_progress(self):
        """Test brief generation reports progress"""
        callback = Mock()

        with patch('packages.orchestrator.orchestrator.BriefOrchestrator._fetch_all_data') as mock_fetch:
            mock_fetch.return_value = {}

            with patch('packages.orchestrator.orchestrator.get_llm_client') as mock_llm:
                mock_llm.side_effect = RuntimeError("No LLM")

                orchestrator = BriefOrchestrator(
                    user_id="user123",
                    progress_callback=callback
                )
                await orchestrator.generate_brief()

                # Should have called progress callback multiple times
                assert callback.call_count >= 5

    @pytest.mark.asyncio
    async def test_generate_brief_general_error(self):
        """Test general error in generate_brief is reported"""
        orchestrator = BriefOrchestrator(user_id="user123")
        with patch.object(orchestrator, '_fetch_all_data', side_effect=Exception("Major failure")):
            with pytest.raises(Exception, match="Major failure"):
                await orchestrator.generate_brief()

    @pytest.mark.asyncio
    async def test_generate_brief_all_modules(self):
        """Test brief generation with all standard modules"""
        orchestrator = BriefOrchestrator(user_id="user123")
        
        # Mock all connectors
        with patch('packages.connectors.gmail.GmailConnector.fetch', new_callable=AsyncMock) as m1, \
             patch('packages.connectors.calendar.CalendarConnector.fetch', new_callable=AsyncMock) as m2, \
             patch('packages.connectors.tasks.TasksConnector.fetch', new_callable=AsyncMock) as m3:
            
            m1.return_value = Mock(items=[])
            m2.return_value = Mock(items=[])
            m3.return_value = Mock(items=[])
            
            with patch('packages.orchestrator.orchestrator.get_llm_client', side_effect=Exception("No LLM")):
                bundle = await orchestrator.generate_brief(modules=["gmail", "calendar", "tasks"])
                assert bundle is not None
                assert m1.called
                assert m2.called
                assert m3.called

    @pytest.mark.asyncio
    async def test_synthesize_brief_success(self):
        """Test successful LLM synthesis"""
        orchestrator = BriefOrchestrator(user_id="user123")
        
        mock_llm = AsyncMock()
        with patch('packages.orchestrator.orchestrator.get_llm_client', return_value=mock_llm):
            with patch('packages.orchestrator.orchestrator.BriefSynthesizer') as mock_synth_class:
                mock_synth = mock_synth_class.return_value
                item = create_test_item("item1")
                mock_synth.synthesize_items = AsyncMock(return_value=[item])
                mock_synth.create_module_summary = AsyncMock(return_value="Module summary")
                
                module_results = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=[item])}
                
                final_items, summaries = await orchestrator._synthesize_brief([item], module_results)
                
                assert len(final_items) == 1
                assert summaries["gmail"] == "Module summary"
                mock_synth.synthesize_items.assert_called_once()
                mock_synth.create_module_summary.assert_called_once()


class TestRunBriefGeneration:
    """Test convenience function"""

    @pytest.mark.asyncio
    async def test_run_brief_generation(self):
        """Test run_brief_generation convenience function"""
        with patch('packages.orchestrator.orchestrator.BriefOrchestrator._fetch_all_data') as mock_fetch:
            mock_fetch.return_value = {}

            with patch('packages.orchestrator.orchestrator.get_llm_client') as mock_llm:
                mock_llm.side_effect = RuntimeError("No LLM")

                bundle = await run_brief_generation(user_id="user123")

                assert bundle is not None
                assert bundle.user_id == "user123"

    @pytest.mark.asyncio
    async def test_run_brief_generation_with_all_params(self):
        """Test run_brief_generation with all parameters"""
        callback = Mock()

        with patch('packages.orchestrator.orchestrator.BriefOrchestrator._fetch_all_data') as mock_fetch:
            mock_fetch.return_value = {}

            with patch('packages.orchestrator.orchestrator.get_llm_client') as mock_llm:
                mock_llm.side_effect = RuntimeError("No LLM")

                bundle = await run_brief_generation(
                    user_id="user123",
                    user_preferences={"topics": ["AI"]},
                    since=datetime.now(timezone.utc) - timedelta(hours=12),
                    modules=["gmail"],
                    progress_callback=callback
                )

                assert bundle is not None
