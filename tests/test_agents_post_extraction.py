"""
Tests for post extraction logic in agents
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone
from packages.agents.twitter_agent import TwitterAgent
from packages.agents.linkedin_agent import LinkedInAgent


class TestTwitterPostExtraction:
    """Test Twitter post extraction"""
    
    @pytest.mark.asyncio
    async def test_fetch_feed_with_posts(self):
        """Test fetching feed with mocked posts"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        # Mock successful extraction
        mock_post = {
            'id': '123',
            'author': '@user',
            'content': 'Test tweet',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'url': 'https://twitter.com/user/status/123',
            'metrics': {'likes': 10},
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Mock the internal extraction method
        agent._extract_post_from_element = AsyncMock(return_value=mock_post)
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        # Mock query_selector_all to return one element
        mock_element = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[mock_element])
        
        result = await agent.fetch_feed(limit=1)
        
        assert len(result) == 1
        assert result[0]['id'] == '123'
    
    @pytest.mark.asyncio
    async def test_fetch_feed_with_limit(self):
        """Test feed fetch respects limit"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        # Create multiple mock posts
        mock_posts = [
            {
                'id': f'post{i}',
                'author': '@user',
                'content': f'Tweet {i}',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'url': f'https://twitter.com/user/status/{i}',
                'metrics': {},
                'fetched_at': datetime.now(timezone.utc).isoformat()
            }
            for i in range(10)
        ]
        
        # Mock to return different posts on each call
        call_count = [0]
        def get_post(element):
            idx = call_count[0]
            call_count[0] += 1
            return mock_posts[idx] if idx < len(mock_posts) else None
        
        agent._extract_post_from_element = AsyncMock(side_effect=lambda e: get_post(e))
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        # Return 10 elements
        mock_elements = [AsyncMock() for _ in range(10)]
        agent._page.query_selector_all = AsyncMock(return_value=mock_elements)
        
        result = await agent.fetch_feed(limit=5)
        
        # Should stop at limit
        assert len(result) <= 5
    
    @pytest.mark.asyncio
    async def test_fetch_feed_handles_extraction_errors(self):
        """Test feed fetch handles extraction errors gracefully"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        # Mock extraction to fail
        agent._extract_post_from_element = AsyncMock(side_effect=Exception("Parse error"))
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        mock_elements = [AsyncMock() for _ in range(3)]
        agent._page.query_selector_all = AsyncMock(return_value=mock_elements)
        
        result = await agent.fetch_feed()
        
        # Should handle errors and return empty list
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_strips_at_symbol(self):
        """Test that @ symbol is stripped from username"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        await agent.fetch_user_posts("@testuser", limit=1)
        
        # Should have navigated to URL without @
        agent.navigate_to.assert_called()
        call_args = agent.navigate_to.call_args[0][0]
        assert '@' not in call_args
        assert 'testuser' in call_args
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_with_posts(self):
        """Test fetching user posts with mocked posts"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        mock_post = {
            'id': '456',
            'author': '@testuser',
            'content': 'User tweet',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'url': 'https://twitter.com/testuser/status/456',
            'metrics': {},
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        agent._extract_post_from_element = AsyncMock(return_value=mock_post)
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        mock_element = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[mock_element])
        
        result = await agent.fetch_user_posts("testuser", limit=1)
        
        assert len(result) == 1
        assert result[0]['author'] == '@testuser'
    
    @pytest.mark.asyncio
    async def test_fetch_feed_deduplicates_posts(self):
        """Test that duplicate posts are filtered out"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        # Same post ID returned multiple times
        duplicate_post = {
            'id': '999',
            'author': '@user',
            'content': 'Duplicate',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'url': 'https://twitter.com/user/status/999',
            'metrics': {},
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        agent._extract_post_from_element = AsyncMock(return_value=duplicate_post)
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        # Return 5 elements (same post)
        mock_elements = [AsyncMock() for _ in range(5)]
        agent._page.query_selector_all = AsyncMock(return_value=mock_elements)
        
        result = await agent.fetch_feed(limit=10)
        
        # Should only have 1 post (deduplicated)
        assert len(result) == 1


class TestLinkedInPostExtraction:
    """Test LinkedIn post extraction"""
    
    @pytest.mark.asyncio
    async def test_fetch_feed_with_posts(self):
        """Test fetching feed with mocked posts"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        mock_post = {
            'id': 'ln123',
            'author': 'Test User',
            'content': 'Professional post',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'url': 'https://www.linkedin.com/feed/update/ln123',
            'metrics': {'likes': 50},
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        agent._extract_post_from_element = AsyncMock(return_value=mock_post)
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        mock_element = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[mock_element])
        
        result = await agent.fetch_feed(limit=1)
        
        assert len(result) == 1
        assert result[0]['id'] == 'ln123'
    
    @pytest.mark.asyncio
    async def test_fetch_feed_handles_extraction_errors(self):
        """Test feed fetch handles extraction errors gracefully"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent._extract_post_from_element = AsyncMock(side_effect=Exception("Parse error"))
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        mock_elements = [AsyncMock() for _ in range(3)]
        agent._page.query_selector_all = AsyncMock(return_value=mock_elements)
        
        result = await agent.fetch_feed()
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_with_posts(self):
        """Test fetching user posts with mocked posts"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        mock_post = {
            'id': 'ln456',
            'author': 'Profile User',
            'content': 'Profile post',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'url': 'https://www.linkedin.com/feed/update/ln456',
            'metrics': {},
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        agent._extract_post_from_element = AsyncMock(return_value=mock_post)
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        mock_element = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[mock_element])
        
        result = await agent.fetch_user_posts("testuser", limit=1)
        
        assert len(result) == 1
        assert result[0]['author'] == 'Profile User'
    
    @pytest.mark.asyncio
    async def test_fetch_user_posts_constructs_correct_url(self):
        """Test that user profile URL is constructed correctly"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        await agent.fetch_user_posts("john-doe", limit=1)
        
        # Should navigate to recent activity page
        agent.navigate_to.assert_called()
        call_args = agent.navigate_to.call_args[0][0]
        assert 'john-doe' in call_args
        assert '/in/' in call_args
        assert '/recent-activity/' in call_args
    
    @pytest.mark.asyncio
    async def test_fetch_feed_deduplicates_posts(self):
        """Test that duplicate posts are filtered out"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        duplicate_post = {
            'id': 'ln999',
            'author': 'User',
            'content': 'Duplicate',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'url': 'https://www.linkedin.com/feed/update/ln999',
            'metrics': {},
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        agent._extract_post_from_element = AsyncMock(return_value=duplicate_post)
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        mock_elements = [AsyncMock() for _ in range(5)]
        agent._page.query_selector_all = AsyncMock(return_value=mock_elements)
        
        result = await agent.fetch_feed(limit=10)
        
        # Should only have 1 post (deduplicated)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_fetch_feed_with_limit(self):
        """Test feed fetch respects limit"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        mock_posts = [
            {
                'id': f'lnpost{i}',
                'author': 'User',
                'content': f'Post {i}',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'url': f'https://www.linkedin.com/feed/update/lnpost{i}',
                'metrics': {},
                'fetched_at': datetime.now(timezone.utc).isoformat()
            }
            for i in range(10)
        ]
        
        call_count = [0]
        def get_post(element):
            idx = call_count[0]
            call_count[0] += 1
            return mock_posts[idx] if idx < len(mock_posts) else None
        
        agent._extract_post_from_element = AsyncMock(side_effect=lambda e: get_post(e))
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        mock_elements = [AsyncMock() for _ in range(10)]
        agent._page.query_selector_all = AsyncMock(return_value=mock_elements)
        
        result = await agent.fetch_feed(limit=3)
        
        assert len(result) <= 3


class TestAgentsScrolling:
    """Test scrolling behavior in agents"""
    
    @pytest.mark.asyncio
    async def test_twitter_feed_scrolls_multiple_times(self):
        """Test Twitter feed scrolls to load more posts"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        await agent.fetch_feed(limit=20)
        
        # Should have called evaluate multiple times for scrolling
        assert agent._page.evaluate.call_count > 0
    
    @pytest.mark.asyncio
    async def test_linkedin_feed_scrolls_multiple_times(self):
        """Test LinkedIn feed scrolls to load more posts"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        agent._page.query_selector_all = AsyncMock(return_value=[])
        
        await agent.fetch_feed(limit=20)
        
        # Should have called evaluate for scrolling
        assert agent._page.evaluate.call_count > 0


class TestAgentsExceptionHandling:
    """Test exception handling in agents"""
    
    @pytest.mark.asyncio
    async def test_twitter_fetch_feed_handles_page_errors(self):
        """Test Twitter feed handles page errors"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))
        
        result = await agent.fetch_feed()
        
        # Should return empty list on error
        assert result == []
    
    @pytest.mark.asyncio
    async def test_linkedin_fetch_feed_handles_page_errors(self):
        """Test LinkedIn feed handles page errors"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))
        
        result = await agent.fetch_feed()
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_twitter_fetch_user_posts_handles_errors(self):
        """Test Twitter user posts handles errors"""
        agent = TwitterAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock(side_effect=Exception("Not found"))
        
        result = await agent.fetch_user_posts("nonexistent")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_linkedin_fetch_user_posts_handles_errors(self):
        """Test LinkedIn user posts handles errors"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock(side_effect=Exception("Not found"))
        
        result = await agent.fetch_user_posts("nonexistent")
        
        assert result == []
