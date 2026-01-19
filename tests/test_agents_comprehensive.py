"""
Comprehensive tests for agents module - Target 80%+ coverage
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from packages.agents.base import BrowserAgent
from packages.agents.twitter_agent import TwitterAgent
from packages.agents.linkedin_agent import LinkedInAgent


class TestBrowserAgentBase:
    """Test BrowserAgent base class"""
    
    def test_browser_agent_is_abstract(self):
        """Test that BrowserAgent cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BrowserAgent()
    
    def test_browser_agent_init_defaults(self):
        """Test BrowserAgent initialization with defaults"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        assert agent.headless == True
        assert agent.timeout == 30000
        assert agent._browser is None
        assert agent._context is None
        assert agent._page is None
    
    def test_browser_agent_init_custom(self):
        """Test BrowserAgent initialization with custom values"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent(headless=False, timeout=60000)
        assert agent.headless == False
        assert agent.timeout == 60000
    
    def test_format_post_basic(self):
        """Test _format_post with basic fields"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        post = agent._format_post(
            post_id="123",
            author="user",
            content="Test content"
        )
        
        assert post['id'] == "123"
        assert post['author'] == "user"
        assert post['content'] == "Test content"
        assert post['timestamp'] is None
        assert post['url'] is None
        assert post['metrics'] == {}
        assert 'fetched_at' in post
    
    def test_format_post_with_all_fields(self):
        """Test _format_post with all fields"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        timestamp = datetime.now(timezone.utc)
        metrics = {'likes': 100, 'retweets': 50}
        
        post = agent._format_post(
            post_id="456",
            author="testuser",
            content="Full test content",
            timestamp=timestamp,
            url="https://example.com/post/456",
            metrics=metrics
        )
        
        assert post['id'] == "456"
        assert post['author'] == "testuser"
        assert post['content'] == "Full test content"
        assert post['timestamp'] == timestamp.isoformat()
        assert post['url'] == "https://example.com/post/456"
        assert post['metrics'] == metrics
    
    def test_format_post_with_empty_metrics(self):
        """Test _format_post with None metrics"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        post = agent._format_post(
            post_id="789",
            author="user",
            content="Content",
            metrics=None
        )
        
        assert post['metrics'] == {}
    
    @pytest.mark.asyncio
    async def test_navigate_to_without_browser(self):
        """Test navigate_to raises error when browser not started"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        with pytest.raises(RuntimeError, match="Browser not started"):
            await agent.navigate_to("https://example.com")
    
    @pytest.mark.asyncio
    async def test_wait_for_selector_without_browser(self):
        """Test wait_for_selector raises error when browser not started"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        with pytest.raises(RuntimeError, match="Browser not started"):
            await agent.wait_for_selector(".test")
    
    @pytest.mark.asyncio
    async def test_extract_text_without_browser(self):
        """Test extract_text raises error when browser not started"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        with pytest.raises(RuntimeError, match="Browser not started"):
            await agent.extract_text(".test")
    
    @pytest.mark.asyncio
    async def test_extract_all_text_without_browser(self):
        """Test extract_all_text raises error when browser not started"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        with pytest.raises(RuntimeError, match="Browser not started"):
            await agent.extract_all_text(".test")
    
    @pytest.mark.asyncio
    async def test_screenshot_without_browser(self):
        """Test screenshot raises error when browser not started"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        with pytest.raises(RuntimeError, match="Browser not started"):
            await agent.screenshot("test.png")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test context manager calls start and stop"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials): return True
            async def fetch_feed(self, limit=20, since=None): return []
            async def fetch_user_posts(self, username, limit=20): return []
            
        agent = TestAgent()
        with patch.object(agent, 'start', new_callable=AsyncMock) as mock_start:
            with patch.object(agent, 'stop', new_callable=AsyncMock) as mock_stop:
                async with agent as a:
                    assert a == agent
                mock_start.assert_called_once()
                mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_success(self):
        """Test successful start and cleanup"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials): return True
            async def fetch_feed(self, limit=20, since=None): return []
            async def fetch_user_posts(self, username, limit=20): return []
            
        agent = TestAgent()
        with patch('playwright.async_api.async_playwright') as mock_pw:
            mock_instance = AsyncMock()
            mock_pw.return_value.start = AsyncMock(return_value=mock_instance)
            mock_instance.chromium.launch = AsyncMock()
            
            await agent.start()
            assert agent._playwright is not None
            # Basic cleanup test
            await agent.stop()

    @pytest.mark.asyncio
    async def test_start_no_playwright(self):
        """Test RuntimeError when playwright missing"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials): return True
            async def fetch_feed(self, limit=20, since=None): return []
            async def fetch_user_posts(self, username, limit=20): return []
            
        agent = TestAgent()
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError, match="Playwright not installed"):
                await agent.start()


class TestTwitterAgent:
    """Test TwitterAgent"""
    
    def test_twitter_agent_init_default(self):
        """Test TwitterAgent initialization with defaults"""
        agent = TwitterAgent()
        assert agent.headless == True
        assert agent.timeout == 30000
        assert agent.BASE_URL == "https://twitter.com"
    
    def test_twitter_agent_init_custom(self):
        """Test TwitterAgent initialization with custom values"""
        agent = TwitterAgent(headless=False, timeout=45000)
        assert agent.headless == False
        assert agent.timeout == 45000
    
    def test_twitter_agent_base_url(self):
        """Test TwitterAgent has correct base URL"""
        agent = TwitterAgent()
        assert agent.BASE_URL == "https://twitter.com"
    
    @pytest.mark.asyncio
    async def test_twitter_login_without_browser(self):
        """Test Twitter login raises error when browser not started"""
        agent = TwitterAgent()
        with pytest.raises(RuntimeError, match="Browser not started"):
            await agent.login({'username': 'test', 'password': 'test'})
    
    def test_twitter_format_post(self):
        """Test Twitter post formatting"""
        agent = TwitterAgent()
        timestamp = datetime.now(timezone.utc)
        
        post = agent._format_post(
            post_id="tweet123",
            author="@testuser",
            content="Test tweet content",
            timestamp=timestamp,
            url="https://twitter.com/testuser/status/tweet123",
            metrics={'likes': 50, 'retweets': 10, 'replies': 5}
        )
        
        assert post['id'] == "tweet123"
        assert post['author'] == "@testuser"
        assert post['content'] == "Test tweet content"
        assert post['metrics']['likes'] == 50
        assert post['metrics']['retweets'] == 10
        assert post['metrics']['replies'] == 5
    
    @pytest.mark.asyncio
    async def test_twitter_fetch_feed_without_browser(self):
        """Test fetch_feed fails gracefully without browser"""
        agent = TwitterAgent()
        # Should raise error or handle gracefully
        try:
            await agent.fetch_feed()
        except RuntimeError:
            pass  # Expected
    
    @pytest.mark.asyncio
    async def test_twitter_fetch_user_posts_without_browser(self):
        """Test fetch_user_posts fails gracefully without browser"""
        agent = TwitterAgent()
        try:
            await agent.fetch_user_posts("testuser")
        except RuntimeError:
            pass  # Expected


class TestLinkedInAgent:
    """Test LinkedInAgent"""
    
    def test_linkedin_agent_init_default(self):
        """Test LinkedInAgent initialization with defaults"""
        agent = LinkedInAgent()
        assert agent.headless == True
        assert agent.timeout == 30000
        assert agent.BASE_URL == "https://www.linkedin.com"
    
    def test_linkedin_agent_init_custom(self):
        """Test LinkedInAgent initialization with custom values"""
        agent = LinkedInAgent(headless=False, timeout=50000)
        assert agent.headless == False
        assert agent.timeout == 50000
    
    def test_linkedin_agent_base_url(self):
        """Test LinkedInAgent has correct base URL"""
        agent = LinkedInAgent()
        assert agent.BASE_URL == "https://www.linkedin.com"
    
    @pytest.mark.asyncio
    async def test_linkedin_login_without_browser(self):
        """Test LinkedIn login raises error when browser not started"""
        agent = LinkedInAgent()
        with pytest.raises(RuntimeError, match="Browser not started"):
            await agent.login({'email': 'test@example.com', 'password': 'test'})
    
    def test_linkedin_format_post(self):
        """Test LinkedIn post formatting"""
        agent = LinkedInAgent()
        timestamp = datetime.now(timezone.utc)
        
        post = agent._format_post(
            post_id="post456",
            author="Test User",
            content="Professional update here",
            timestamp=timestamp,
            url="https://www.linkedin.com/feed/update/post456",
            metrics={'likes': 200, 'comments': 30, 'shares': 15}
        )
        
        assert post['id'] == "post456"
        assert post['author'] == "Test User"
        assert post['content'] == "Professional update here"
        assert post['metrics']['likes'] == 200
        assert post['metrics']['comments'] == 30
        assert post['metrics']['shares'] == 15
    
    @pytest.mark.asyncio
    async def test_linkedin_fetch_feed_without_browser(self):
        """Test fetch_feed fails gracefully without browser"""
        agent = LinkedInAgent()
        try:
            await agent.fetch_feed()
        except RuntimeError:
            pass  # Expected
    
    @pytest.mark.asyncio
    async def test_linkedin_fetch_user_posts_without_browser(self):
        """Test fetch_user_posts fails gracefully without browser"""
        agent = LinkedInAgent()
        try:
            await agent.fetch_user_posts("testuser")
        except RuntimeError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_linkedin_login_failure(self):
        """Test LinkedIn login failure handling"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector.side_effect = Exception("Login failed")
        
        result = await agent.login({'email': 'e', 'password': 'p'})
        assert result is False

    @pytest.mark.asyncio
    async def test_linkedin_fetch_feed_failure(self):
        """Test LinkedIn fetch_feed error handling"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector.side_effect = Exception("Feed failed")
        
        result = await agent.fetch_feed()
        assert result == []

    def test_linkedin_parse_metric_error(self):
        """Test parsing of unusual metrics"""
        agent = LinkedInAgent()
        assert agent._parse_metric("invalid") == 0
        assert agent._parse_metric("1K") == 1000
        assert agent._parse_metric("1M") == 1000000


class TestAgentsWithMockedBrowser:
    """Test agents with simpler mocking"""
    
    @pytest.mark.asyncio
    async def test_navigate_to_with_mocked_page(self):
        """Test navigate_to with mocked page"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        # Mock the page
        agent._page = AsyncMock()
        agent._page.goto = AsyncMock()
        
        await agent.navigate_to("https://example.com")
        agent._page.goto.assert_called_once_with("https://example.com", timeout=30000)
    
    @pytest.mark.asyncio
    async def test_wait_for_selector_with_mocked_page(self):
        """Test wait_for_selector with mocked page"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        
        await agent.wait_for_selector(".test-selector")
        agent._page.wait_for_selector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_wait_for_selector_custom_timeout(self):
        """Test wait_for_selector with custom timeout"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        
        await agent.wait_for_selector(".test", timeout=60000)
        agent._page.wait_for_selector.assert_called_once_with(".test", timeout=60000)
    
    @pytest.mark.asyncio
    async def test_extract_text_with_element(self):
        """Test extract_text with element found"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        mock_element = AsyncMock()
        mock_element.inner_text = AsyncMock(return_value="Test text")
        agent._page = AsyncMock()
        agent._page.query_selector = AsyncMock(return_value=mock_element)
        
        text = await agent.extract_text(".selector")
        assert text == "Test text"
    
    @pytest.mark.asyncio
    async def test_extract_text_no_element(self):
        """Test extract_text with no element found"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        agent._page = AsyncMock()
        agent._page.query_selector = AsyncMock(return_value=None)
        
        text = await agent.extract_text(".nonexistent")
        assert text == ""
    
    @pytest.mark.asyncio
    async def test_extract_all_text(self):
        """Test extract_all_text"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        mock_elem1 = AsyncMock()
        mock_elem1.inner_text = AsyncMock(return_value="Text 1")
        mock_elem2 = AsyncMock()
        mock_elem2.inner_text = AsyncMock(return_value="Text 2")
        agent._page = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[mock_elem1, mock_elem2])
        
        texts = await agent.extract_all_text(".items")
        assert len(texts) == 2
        assert texts[0] == "Text 1"
        assert texts[1] == "Text 2"
    
    @pytest.mark.asyncio
    async def test_screenshot_with_mocked_page(self):
        """Test screenshot with mocked page"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        agent._page = AsyncMock()
        agent._page.screenshot = AsyncMock()
        
        await agent.screenshot("/tmp/test.png")
        agent._page.screenshot.assert_called_once_with(path="/tmp/test.png")
    
    @pytest.mark.asyncio
    async def test_stop_with_all_resources(self):
        """Test stop cleans up all resources"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        agent._page = AsyncMock()
        agent._page.close = AsyncMock()
        agent._context = AsyncMock()
        agent._context.close = AsyncMock()
        agent._browser = AsyncMock()
        agent._browser.close = AsyncMock()
        agent._playwright = AsyncMock()
        agent._playwright.stop = AsyncMock()
        
        await agent.stop()
        
        agent._page.close.assert_called_once()
        agent._context.close.assert_called_once()
        agent._browser.close.assert_called_once()
        agent._playwright.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_with_partial_resources(self):
        """Test stop works with only some resources initialized"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        agent._page = AsyncMock()
        agent._page.close = AsyncMock()
        # _context and _browser are None
        
        await agent.stop()  # Should not raise
        agent._page.close.assert_called_once()

class TestAgentsEdgeCases:
    """Test edge cases and error handling"""
    
    def test_format_post_with_none_timestamp(self):
        """Test _format_post handles None timestamp"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        post = agent._format_post(
            post_id="1",
            author="user",
            content="content",
            timestamp=None
        )
        
        assert post['timestamp'] is None
    
    def test_format_post_with_empty_content(self):
        """Test _format_post handles empty content"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        post = agent._format_post(
            post_id="1",
            author="user",
            content=""
        )
        
        assert post['content'] == ""
    
    def test_format_post_with_special_characters(self):
        """Test _format_post handles special characters"""
        class TestAgent(BrowserAgent):
            async def login(self, credentials):
                return True
            async def fetch_feed(self, limit=20, since=None):
                return []
            async def fetch_user_posts(self, username, limit=20):
                return []
        
        agent = TestAgent()
        post = agent._format_post(
            post_id="1",
            author="user@#$%",
            content="Test <>&\" content"
        )
        
        assert post['author'] == "user@#$%"
        assert post['content'] == "Test <>&\" content"
    
    def test_twitter_agent_multiple_instances(self):
        """Test creating multiple Twitter agent instances"""
        agent1 = TwitterAgent()
        agent2 = TwitterAgent(headless=False)
        
        assert agent1.headless == True
        assert agent2.headless == False
        assert agent1 is not agent2
    
    def test_linkedin_agent_multiple_instances(self):
        """Test creating multiple LinkedIn agent instances"""
        agent1 = LinkedInAgent()
        agent2 = LinkedInAgent(timeout=60000)
        
        assert agent1.timeout == 30000
        assert agent2.timeout == 60000
        assert agent1 is not agent2
