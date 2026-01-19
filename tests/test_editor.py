"""
Comprehensive tests for editor module (llm_client.py and synthesizer.py)
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import os

from packages.editor.llm_client import (
    LLMClient,
    ClaudeClient,
    OllamaClient,
    OpenAIClient,
    get_llm_client,
)
from packages.editor.synthesizer import (
    BriefSynthesizer,
    synthesize_brief,
)
from packages.shared.schemas import (
    BriefItem, ModuleResult, NoveltyInfo, RankingScores, Entity
)


def create_test_item(
    item_ref: str = "test_item",
    source: str = "gmail",
    item_type: str = "email",
    title: str = "Test Title",
    summary: str = "Test Summary",
) -> BriefItem:
    """Helper to create test items"""
    timestamp = datetime.now(timezone.utc).isoformat()
    return BriefItem(
        item_ref=item_ref,
        source=source,
        type=item_type,
        timestamp_utc=timestamp,
        title=title,
        summary=summary,
        why_it_matters="",
        entities=[],
        novelty=NoveltyInfo(
            label="NEW",
            reason="Test",
            first_seen_utc=timestamp
        ),
        ranking=RankingScores(
            relevance_score=0.7,
            urgency_score=0.8,
            credibility_score=0.9,
            impact_score=0.7,
            actionability_score=0.6,
            final_score=0.75
        ),
        evidence=[],
        suggested_actions=[]
    )


class TestClaudeClient:
    """Test ClaudeClient"""

    def test_init_default(self):
        """Test default initialization"""
        client = ClaudeClient()
        assert client.model == "claude-3-sonnet-20240229"
        assert client._client is None

    def test_init_with_model(self):
        """Test initialization with custom model"""
        client = ClaudeClient(model="claude-3-opus-20240229")
        assert client.model == "claude-3-opus-20240229"

    def test_init_with_api_key(self):
        """Test initialization with API key"""
        client = ClaudeClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_is_available_with_key(self):
        """Test availability with API key"""
        client = ClaudeClient(api_key="test_key")
        assert client.is_available() is True

    def test_is_available_without_key(self):
        """Test availability without API key"""
        with patch.dict(os.environ, {}, clear=True):
            client = ClaudeClient(api_key=None)
            client.api_key = None  # Clear any env-based key
            assert client.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_not_available(self):
        """Test generate raises when not available"""
        client = ClaudeClient(api_key=None)
        client.api_key = None

        with pytest.raises(RuntimeError, match="Claude API key not configured"):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation"""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text="Generated text")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            client = ClaudeClient(api_key="test_key")
            result = await client.generate("Test prompt", system_prompt="System")

            assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_generate_error(self):
        """Test generate handles API errors"""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_anthropic.side_effect = Exception("API Error")

            client = ClaudeClient(api_key="test_key")

            with pytest.raises(RuntimeError, match="Claude API error"):
                await client.generate("Test prompt")


class TestOllamaClient:
    """Test OllamaClient"""

    def test_init_default(self):
        """Test default initialization"""
        client = OllamaClient()
        assert client.model == "llama3.2"
        assert "localhost:11434" in client.base_url

    def test_init_with_model(self):
        """Test initialization with custom model"""
        client = OllamaClient(model="mistral")
        assert client.model == "mistral"

    def test_init_with_base_url(self):
        """Test initialization with custom base URL"""
        client = OllamaClient(base_url="http://custom:11434")
        assert client.base_url == "http://custom:11434"

    def test_is_available_success(self):
        """Test availability check success"""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            client = OllamaClient()
            assert client.is_available() is True

    def test_is_available_failure(self):
        """Test availability check failure"""
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            client = OllamaClient()
            assert client.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_not_available(self):
        """Test generate when Ollama not available"""
        with patch.object(OllamaClient, 'is_available', return_value=False):
            client = OllamaClient()

            with pytest.raises(RuntimeError, match="Ollama not available"):
                await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation"""
        with patch.object(OllamaClient, 'is_available', return_value=True):
            with patch('httpx.AsyncClient') as mock_async_client:
                mock_response = Mock()
                mock_response.json.return_value = {"response": "Generated text"}
                mock_response.raise_for_status = Mock()

                mock_client_instance = AsyncMock()
                mock_client_instance.post.return_value = mock_response
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_async_client.return_value = mock_client_instance

                client = OllamaClient()
                result = await client.generate("Test prompt", system_prompt="System")

                assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_generate_error(self):
        """Test generate handles errors"""
        with patch.object(OllamaClient, 'is_available', return_value=True):
            with patch('httpx.AsyncClient') as mock_async_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.post.side_effect = Exception("Connection error")
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_async_client.return_value = mock_client_instance

                client = OllamaClient()

                with pytest.raises(RuntimeError, match="Ollama API error"):
                    await client.generate("Test prompt")


class TestOpenAIClient:
    """Test OpenAIClient"""

    def test_init_default(self):
        """Test default initialization"""
        client = OpenAIClient()
        assert client.model == "gpt-4"
        assert client._client is None

    def test_init_with_model(self):
        """Test initialization with custom model"""
        client = OpenAIClient(model="gpt-4-turbo")
        assert client.model == "gpt-4-turbo"

    def test_init_with_api_key(self):
        """Test initialization with API key"""
        client = OpenAIClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_is_available_with_key(self):
        """Test availability with API key"""
        client = OpenAIClient(api_key="test_key")
        assert client.is_available() is True

    def test_is_available_without_key(self):
        """Test availability without API key"""
        with patch.dict(os.environ, {}, clear=True):
            client = OpenAIClient(api_key=None)
            client.api_key = None
            assert client.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_not_available(self):
        """Test generate raises when not available"""
        client = OpenAIClient(api_key=None)
        client.api_key = None

        with pytest.raises(RuntimeError, match="OpenAI API key not configured"):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Generated text"))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = OpenAIClient(api_key="test_key")
            result = await client.generate("Test prompt", system_prompt="System")

            assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test generation with system prompt includes it in messages"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = OpenAIClient(api_key="test_key")
            await client.generate("User prompt", system_prompt="Be helpful")

            # Verify the messages included system prompt
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs.get('messages', [])
            assert any(m.get('role') == 'system' for m in messages)


class TestGetLLMClient:
    """Test get_llm_client factory function"""

    def test_get_claude_client_explicit(self):
        """Test explicitly requesting Claude client"""
        with patch.object(ClaudeClient, 'is_available', return_value=True):
            client = get_llm_client(provider="claude", api_key="test_key")
            assert isinstance(client, ClaudeClient)

    def test_get_ollama_client_explicit(self):
        """Test explicitly requesting Ollama client"""
        with patch.object(OllamaClient, 'is_available', return_value=True):
            client = get_llm_client(provider="ollama")
            assert isinstance(client, OllamaClient)

    def test_get_openai_client_explicit(self):
        """Test explicitly requesting OpenAI client"""
        with patch.object(OpenAIClient, 'is_available', return_value=True):
            client = get_llm_client(provider="openai", api_key="test_key")
            assert isinstance(client, OpenAIClient)

    def test_auto_detect_ollama(self):
        """Test auto-detection finds Ollama"""
        with patch.object(OllamaClient, 'is_available', return_value=True):
            client = get_llm_client()
            assert isinstance(client, OllamaClient)

    def test_auto_detect_fallback_to_claude(self):
        """Test auto-detection falls back to Claude"""
        with patch.object(OllamaClient, 'is_available', return_value=False):
            with patch.object(ClaudeClient, 'is_available', return_value=True):
                client = get_llm_client()
                assert isinstance(client, ClaudeClient)

    def test_auto_detect_fallback_to_openai(self):
        """Test auto-detection falls back to OpenAI"""
        with patch.object(OllamaClient, 'is_available', return_value=False):
            with patch.object(ClaudeClient, 'is_available', return_value=False):
                with patch.object(OpenAIClient, 'is_available', return_value=True):
                    client = get_llm_client()
                    assert isinstance(client, OpenAIClient)

    def test_no_provider_available(self):
        """Test error when no provider available"""
        with patch.object(OllamaClient, 'is_available', return_value=False):
            with patch.object(ClaudeClient, 'is_available', return_value=False):
                with patch.object(OpenAIClient, 'is_available', return_value=False):
                    with pytest.raises(RuntimeError, match="No LLM provider available"):
                        get_llm_client()

    def test_get_client_with_custom_model(self):
        """Test getting client with custom model"""
        with patch.object(ClaudeClient, 'is_available', return_value=True):
            client = get_llm_client(provider="claude", model="claude-3-opus", api_key="key")
            assert client.model == "claude-3-opus"


class TestBriefSynthesizer:
    """Test BriefSynthesizer"""

    def test_init_with_client(self):
        """Test initialization with LLM client"""
        mock_client = Mock()
        synthesizer = BriefSynthesizer(llm_client=mock_client)
        assert synthesizer.llm == mock_client

    def test_init_with_preferences(self):
        """Test initialization with preferences"""
        mock_client = Mock()
        prefs = {"topics": ["AI"], "vip_people": ["boss@company.com"]}
        synthesizer = BriefSynthesizer(llm_client=mock_client, user_preferences=prefs)
        assert synthesizer.preferences == prefs

    @pytest.mark.asyncio
    async def test_add_why_it_matters_success(self):
        """Test successful why_it_matters generation"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="This matters because...")

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        item = create_test_item()

        result = await synthesizer.add_why_it_matters(item)

        assert result.why_it_matters == "This matters because..."

    @pytest.mark.asyncio
    async def test_add_why_it_matters_error_fallback(self):
        """Test fallback when LLM fails"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=Exception("LLM error"))

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        item = create_test_item(item_type="email")

        result = await synthesizer.add_why_it_matters(item)

        assert result.why_it_matters == "New email requiring your attention."

    @pytest.mark.asyncio
    async def test_add_why_it_matters_fallback_event(self):
        """Test fallback for event type"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=Exception("LLM error"))

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        item = create_test_item(item_type="event")

        result = await synthesizer.add_why_it_matters(item)

        assert result.why_it_matters == "Upcoming event on your calendar."

    @pytest.mark.asyncio
    async def test_add_why_it_matters_fallback_task(self):
        """Test fallback for task type"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=Exception("LLM error"))

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        item = create_test_item(item_type="task")

        result = await synthesizer.add_why_it_matters(item)

        assert result.why_it_matters == "Pending task that needs completion."

    @pytest.mark.asyncio
    async def test_add_why_it_matters_fallback_other(self):
        """Test fallback for other types"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=Exception("LLM error"))

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        item = create_test_item(item_type="social_post")

        result = await synthesizer.add_why_it_matters(item)

        assert result.why_it_matters == "New item for your review."

    @pytest.mark.asyncio
    async def test_synthesize_items_batch(self):
        """Test batch synthesis"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Important")

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        items = [create_test_item(f"item{i}") for i in range(3)]

        results = await synthesizer.synthesize_items(items)

        assert len(results) == 3
        assert all(item.why_it_matters == "Important" for item in results)

    @pytest.mark.asyncio
    async def test_synthesize_items_handles_exceptions(self):
        """Test batch synthesis handles individual exceptions"""
        mock_client = AsyncMock()
        # First call succeeds, second fails, third succeeds
        mock_client.generate = AsyncMock(side_effect=[
            "Important 1",
            Exception("Error"),
            "Important 3"
        ])

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        items = [create_test_item(f"item{i}") for i in range(3)]

        results = await synthesizer.synthesize_items(items)

        # Should have results (may include fallbacks for failed items)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_create_module_summary_empty_items(self):
        """Test module summary with no items"""
        mock_client = AsyncMock()
        synthesizer = BriefSynthesizer(llm_client=mock_client)

        result = await synthesizer.create_module_summary(
            module_name="gmail",
            items=[],
            new_count=0,
            updated_count=0
        )

        assert "No new updates" in result

    @pytest.mark.asyncio
    async def test_create_module_summary_success(self):
        """Test successful module summary generation"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="3 new emails, 1 urgent")

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        items = [create_test_item(f"item{i}") for i in range(3)]

        result = await synthesizer.create_module_summary(
            module_name="gmail",
            items=items,
            new_count=3,
            updated_count=0
        )

        assert result == "3 new emails, 1 urgent"

    @pytest.mark.asyncio
    async def test_create_module_summary_fallback(self):
        """Test module summary fallback on error"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(side_effect=Exception("LLM error"))

        synthesizer = BriefSynthesizer(llm_client=mock_client)
        items = [create_test_item(f"item{i}") for i in range(3)]
        # Set high urgency for some items
        items[0].ranking.urgency_score = 0.9

        result = await synthesizer.create_module_summary(
            module_name="gmail",
            items=items,
            new_count=3,
            updated_count=0
        )

        # Should use fallback format
        assert "gmail" in result.lower()
        assert "new" in result


class TestSynthesizeBriefFunction:
    """Test synthesize_brief convenience function"""

    @pytest.mark.asyncio
    async def test_synthesize_brief_basic(self):
        """Test basic synthesize_brief"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Test summary")

        items = [create_test_item("item1")]
        modules = {
            "gmail": ModuleResult(
                status="ok",
                summary="1 new",
                new_count=1,
                updated_count=0,
                items=items
            )
        }

        result = await synthesize_brief(
            items=items,
            modules=modules,
            llm_client=mock_client
        )

        assert "items" in result
        assert "module_summaries" in result

    @pytest.mark.asyncio
    async def test_synthesize_brief_with_preferences(self):
        """Test synthesize_brief with preferences"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Personalized summary")

        items = [create_test_item("item1")]
        modules = {"gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items)}
        prefs = {"topics": ["AI"]}

        result = await synthesize_brief(
            items=items,
            modules=modules,
            user_preferences=prefs,
            llm_client=mock_client
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_synthesize_brief_empty_module_items(self):
        """Test synthesize_brief skips modules with no items"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Summary")

        items = [create_test_item("item1")]
        modules = {
            "gmail": ModuleResult(status="ok", summary="1 new", new_count=1, updated_count=0, items=items),
            "calendar": ModuleResult(status="ok", summary="0 new", new_count=0, updated_count=0, items=[])
        }

        result = await synthesize_brief(
            items=items,
            modules=modules,
            llm_client=mock_client
        )

        # Should only have summary for gmail (calendar has no items)
        assert "gmail" in result["module_summaries"]
