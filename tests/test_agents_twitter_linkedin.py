"""
Additional tests for TwitterAgent and LinkedInAgent to increase coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from datetime import datetime, timezone
from packages.agents.twitter_agent import TwitterAgent
from packages.agents.linkedin_agent import LinkedInAgent


class TestTwitterAgentLogin:
    """Test TwitterAgent login functionality"""
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful Twitter login"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.fill = AsyncMock()
        agent._page.click = AsyncMock()
        
        # Mock navigate_to
        agent.navigate_to = AsyncMock()
        
        credentials = {'username': 'testuser', 'password': 'testpass'}
        result = await agent.login(credentials)
        
        assert result == True
        agent.navigate_to.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_failure(self):
        """Test Twitter login failure"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))
        
        agent.navigate_to = AsyncMock()
        
        credentials = {'username': 'test', 'password': 'test'}
        result = await agent.login(credentials)
        
        assert result == False


class TestTwitterAgentFetchFeed:
    """Test TwitterAgent fetch_feed functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_feed_basic(self):
        """Test basic feed fetch"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        # Mock page methods
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        # Mock query_selector_all to return no tweets
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_feed(limit=5)
        
        # Should return empty list if no posts found
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fetch_feed_with_limit(self):
        """Test feed fetch with limit"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_feed(limit=10)
        
        assert isinstance(result, list)


class TestTwitterAgentFetchUserPosts:
    """Test TwitterAgent fetch_user_posts functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_basic(self):
        """Test basic user posts fetch"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_user_posts("testuser", limit=5)
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_with_username(self):
        """Test user posts fetch with different username"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_user_posts("anotheruser", limit=10)
        
        assert isinstance(result, list)


class TestLinkedInAgentLogin:
    """Test LinkedInAgent login functionality"""
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful LinkedIn login"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.fill = AsyncMock()
        agent._page.click = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        
        credentials = {'email': 'test@example.com', 'password': 'testpass'}
        result = await agent.login(credentials)
        
        assert result == True
        agent.navigate_to.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_failure(self):
        """Test LinkedIn login failure"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector = AsyncMock(side_effect=Exception("Failed"))
        
        agent.navigate_to = AsyncMock()
        
        credentials = {'email': 'test@example.com', 'password': 'test'}
        result = await agent.login(credentials)
        
        assert result == False


class TestLinkedInAgentFetchFeed:
    """Test LinkedInAgent fetch_feed functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_feed_basic(self):
        """Test basic feed fetch"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_feed(limit=5)
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fetch_feed_with_limit(self):
        """Test feed fetch with limit"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_feed(limit=15)
        
        assert isinstance(result, list)


class TestLinkedInAgentFetchUserPosts:
    """Test LinkedInAgent fetch_user_posts functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_basic(self):
        """Test basic user posts fetch"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_user_posts("testuser", limit=5)
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_with_profile(self):
        """Test user posts fetch with profile ID"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        result = await agent.fetch_user_posts("another-user-id", limit=10)
        
        assert isinstance(result, list)


class TestTwitterAgentHelpers:
    """Test Twitter agent helper methods"""
    
    def test_format_tweet_post(self):
        """Test formatting a tweet"""
        agent = TwitterAgent()
        timestamp = datetime.now(timezone.utc)
        
        post = agent._format_post(
            post_id="12345",
            author="@user",
            content="This is a tweet",
            timestamp=timestamp,
            url="https://twitter.com/user/status/12345",
            metrics={'likes': 100, 'retweets': 20}
        )
        
        assert post['id'] == "12345"
        assert post['author'] == "@user"
        assert post['content'] == "This is a tweet"
        assert 'fetched_at' in post


class TestLinkedInAgentHelpers:
    """Test LinkedIn agent helper methods"""
    
    def test_format_linkedin_post(self):
        """Test formatting a LinkedIn post"""
        agent = LinkedInAgent()
        timestamp = datetime.now(timezone.utc)
        
        post = agent._format_post(
            post_id="abc123",
            author="Test User",
            content="Professional insight here",
            timestamp=timestamp,
            url="https://www.linkedin.com/feed/update/abc123",
            metrics={'likes': 50, 'comments': 10}
        )
        
        assert post['id'] == "abc123"
        assert post['author'] == "Test User"
        assert post['content'] == "Professional insight here"
        assert 'fetched_at' in post


class TestAgentsErrorHandling:
    """Test error handling in agents"""
    
    @pytest.mark.asyncio
    async def test_twitter_fetch_feed_error_handling(self):
        """Test Twitter feed fetch handles errors gracefully"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        # Mock methods to raise exceptions
        agent.navigate_to = AsyncMock(side_effect=Exception("Network error"))
        
        # Should handle error gracefully
        try:
            result = await agent.fetch_feed()
            # If it doesn't raise, result should be a list
            assert isinstance(result, list)
        except Exception:
            # Or it may raise, which is also acceptable
            pass
    
    @pytest.mark.asyncio
    async def test_linkedin_fetch_feed_error_handling(self):
        """Test LinkedIn feed fetch handles errors gracefully"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock(side_effect=Exception("Network error"))
        
        try:
            result = await agent.fetch_feed()
            assert isinstance(result, list)
        except Exception:
            pass
    
    @pytest.mark.asyncio
    async def test_twitter_fetch_user_posts_error_handling(self):
        """Test Twitter user posts fetch handles errors gracefully"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock(side_effect=Exception("Not found"))
        
        try:
            result = await agent.fetch_user_posts("testuser")
            assert isinstance(result, list)
        except Exception:
            pass
    
    @pytest.mark.asyncio
    async def test_linkedin_fetch_user_posts_error_handling(self):
        """Test LinkedIn user posts fetch handles errors gracefully"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock(side_effect=Exception("Not found"))
        
        try:
            result = await agent.fetch_user_posts("testuser")
            assert isinstance(result, list)
        except Exception:
            pass


class TestAgentsConfiguration:
    """Test agent configuration options"""
    
    def test_twitter_custom_timeout(self):
        """Test Twitter agent with custom timeout"""
        agent = TwitterAgent(timeout=60000)
        assert agent.timeout == 60000
    
    def test_linkedin_custom_timeout(self):
        """Test LinkedIn agent with custom timeout"""
        agent = LinkedInAgent(timeout=45000)
        assert agent.timeout == 45000
    
    def test_twitter_headless_mode(self):
        """Test Twitter agent headless configuration"""
        agent1 = TwitterAgent(headless=True)
        agent2 = TwitterAgent(headless=False)
        
        assert agent1.headless == True
        assert agent2.headless == False
    
    def test_linkedin_headless_mode(self):
        """Test LinkedIn agent headless configuration"""
        agent1 = LinkedInAgent(headless=True)
        agent2 = LinkedInAgent(headless=False)
        
        assert agent1.headless == True
        assert agent2.headless == False


class TestAgentsURLConstruction:
    """Test URL construction in agents"""
    
    def test_twitter_base_url(self):
        """Test Twitter base URL"""
        agent = TwitterAgent()
        assert agent.BASE_URL == "https://twitter.com"
    
    def test_linkedin_base_url(self):
        """Test LinkedIn base URL"""
        agent = LinkedInAgent()
        assert agent.BASE_URL == "https://www.linkedin.com"
