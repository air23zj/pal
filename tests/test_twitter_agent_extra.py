import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from packages.agents.twitter_agent import TwitterAgent

class TestTwitterAgentExtra:
    """Extra tests for TwitterAgent to cover all branches"""

    @pytest.fixture
    def twitter_agent(self):
        return TwitterAgent()
    
    @pytest.fixture
    def mock_page(self):
        page = AsyncMock()
        page.navigate_to = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.query_selector_all = AsyncMock()
        page.click = AsyncMock()
        page.fill = AsyncMock()
        return page

    @pytest.mark.asyncio
    async def test_twitter_login_success(self):
        agent = TwitterAgent()
        agent._page = AsyncMock()
        agent.navigate_to = AsyncMock()
        
        # Test basic success path
        credentials = {'username': 'test@example.com', 'password': 'password123'}
        result = await agent.login(credentials)
        assert result is True
        assert agent._page.fill.call_count == 2
        assert agent._page.click.call_count == 2

    @pytest.mark.asyncio
    async def test_twitter_login_failure(self):
        agent = TwitterAgent()
        agent._page = AsyncMock()
        # Trigger an exception during one of the steps
        agent._page.wait_for_selector.side_effect = Exception("Element not found")
        
        result = await agent.login({'username': 'u', 'password': 'p'})
        assert result is False

    @pytest.mark.asyncio
    async def test_twitter_fetch_feed_with_posts(self):
        agent = TwitterAgent()
        agent._page = AsyncMock()
        agent.navigate_to = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        agent._page.evaluate = AsyncMock()
        
        # Mock finding tweet elements
        mock_element = MagicMock() # Use MagicMock for the element handle itself
        # Mock _extract_post_from_element as instance method mock
        with patch.object(TwitterAgent, '_extract_post_from_element', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {'id': '123', 'content': 'test'}
            
            # Mock query_selector_all
            agent._page.query_selector_all.side_effect = [[mock_element], [], []]
            
            result = await agent.fetch_feed(limit=5)
            assert len(result) == 1
            assert result[0]['id'] == '123'

    @pytest.mark.asyncio
    async def test_twitter_fetch_user_posts_paging(self):
        agent = TwitterAgent()
        agent._page = AsyncMock()
        agent.navigate_to = AsyncMock()
        
        mock_el1 = AsyncMock()
        mock_el2 = AsyncMock()
        
        # Return different elements on different calls to simulate scrolling
        agent._page.query_selector_all.side_effect = [
            [mock_el1],
            [mock_el1, mock_el2],
            [mock_el2]
        ]
        
        idx = 0
        async def mock_extract(el):
            nonlocal idx
            idx += 1
            return {'id': f'tweet_{idx}', 'content': 'scroll test'}
            
        agent._extract_post_from_element = mock_extract
        
        result = await agent.fetch_user_posts("testuser", limit=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_twitter_extract_post_complex(self):
        agent = TwitterAgent()
        mock_element = AsyncMock()
        
        # Mock text content
        mock_text_el = AsyncMock()
        mock_text_el.inner_text.return_value = "Hot take on AI!"
        
        # Mock author
        mock_author_el = AsyncMock()
        mock_author_el.inner_text.return_value = "John Doe\n@johndoe\n·\n1h"
        
        # Mock link/ID
        mock_link_el = AsyncMock()
        mock_link_el.get_attribute.return_value = "/user/status/987654321"
        
        # Mock metrics
        mock_reply = AsyncMock()
        mock_reply.inner_text.return_value = "1.5K"
        mock_retweet = AsyncMock()
        mock_retweet.inner_text.return_value = "200"
        mock_like = AsyncMock()
        mock_like.inner_text.return_value = "5.2M"
        
        def mock_query_selector(selector):
            if "tweetText" in selector: return mock_text_el
            if "User-Name" in selector: return mock_author_el
            if "/status/" in selector: return mock_link_el
            if "reply" in selector: return mock_reply
            if "retweet" in selector: return mock_retweet
            if "like" in selector: return mock_like
            return None
            
        mock_element.query_selector.side_effect = mock_query_selector
        
        result = await agent._extract_post_from_element(mock_element)
        
        assert result['id'] == "987654321"
        assert result['author'] == "@johndoe"
        assert result['content'] == "Hot take on AI!"
        assert result['metrics']['replies'] == 1500
        assert result['metrics']['retweets'] == 200
        assert result['metrics']['likes'] == 5200000

    @pytest.mark.asyncio
    async def test_twitter_browser_not_started(self, twitter_agent):
        """Test that methods raise error if browser not started"""
        # Ensure _page is None
        twitter_agent._page = None
        
        with pytest.raises(RuntimeError, match="Browser not started"):
            await twitter_agent.login({"username": "u", "password": "p"})
            
        with pytest.raises(RuntimeError, match="Browser not started"):
            await twitter_agent.fetch_feed()
            
        with pytest.raises(RuntimeError, match="Browser not started"):
            await twitter_agent.fetch_user_posts("test_user")

    @pytest.mark.asyncio
    async def test_twitter_fetch_feed_general_error(self, twitter_agent, mock_page):
        """Test general error handling in fetch_feed"""
        twitter_agent._page = mock_page
        mock_page.navigate_to.side_effect = Exception("Navigate error")
        
        posts = await twitter_agent.fetch_feed()
        assert posts == []

    @pytest.mark.asyncio
    async def test_twitter_fetch_user_posts_general_error(self, twitter_agent, mock_page):
        """Test general error handling in fetch_user_posts"""
        twitter_agent._page = mock_page
        mock_page.navigate_to.side_effect = Exception("Navigate error")
        
        posts = await twitter_agent.fetch_user_posts("test_user")
        assert posts == []

    @pytest.mark.asyncio
    async def test_twitter_extract_post_metrics_error(self, twitter_agent, mock_page):
        """Test error handling in metrics extraction"""
        twitter_agent._page = mock_page
        
        mock_element = AsyncMock()
        # content
        mock_text_el = AsyncMock()
        mock_text_el.inner_text.return_value = "Tweet content"
        mock_element.query_selector.return_value = mock_text_el
        
        # metrics will raise error when queried or processed
        # e.g. query_selector returns an element that fails on inner_text
        mock_metrics_el = AsyncMock()
        mock_metrics_el.inner_text.side_effect = Exception("Metric Error")
        
        # mock_element.query_selector needs to handle multiple calls
        # 1. tweetText -> mock_text_el
        # 2. User-Name -> None
        # 3. a[href...] -> None
        # 4. reply -> mock_metrics_el
        
        async def side_effect(selector):
            if selector == '[data-testid="tweetText"]': return mock_text_el
            if selector == '[data-testid="reply"]': return mock_metrics_el
            return None
            
        mock_element.query_selector.side_effect = side_effect
        
        post = await twitter_agent._extract_post_from_element(mock_element)
        assert post is not None
        assert 'replies' not in post['metrics'] or post['metrics']['replies'] == 0

    @pytest.mark.asyncio
    async def test_twitter_extract_post_fallback_id(self):
        agent = TwitterAgent()
        mock_element = AsyncMock()
        
        # No link element
        mock_element.query_selector.return_value = None
        
        # But some content
        mock_text_el = AsyncMock()
        mock_text_el.inner_text.return_value = "No link tweet"
        
        mock_element.query_selector.side_effect = lambda s: mock_text_el if "tweetText" in s else None
        
        result = await agent._extract_post_from_element(mock_element)
        assert result['id'].startswith("unknown_")

    def test_twitter_parse_metric_variants(self):
        agent = TwitterAgent()
        assert agent._parse_metric("100") == 100
        assert agent._parse_metric("1.2K") == 1200
        assert agent._parse_metric("3.5M") == 3500000
        assert agent._parse_metric("invalid") == 0
        assert agent._parse_metric("") == 0
        assert agent._parse_metric("   ") == 0

    @pytest.mark.asyncio
    async def test_twitter_extract_post_timestamp_success(self, twitter_agent, mock_page):
        """Test timestamp extraction success"""
        twitter_agent._page = mock_page
        mock_element = AsyncMock()
        
        # Content
        mock_text_el = AsyncMock()
        mock_text_el.inner_text.return_value = "Content"
        
        # Time element
        mock_time_el = AsyncMock()
        mock_time_el.get_attribute.return_value = "2023-11-20T10:00:00.000Z"
        
        async def side_effect(selector):
            if selector == '[data-testid="tweetText"]': return mock_text_el
            if selector == 'time': return mock_time_el
            return None
        
        mock_element.query_selector.side_effect = side_effect
        
        post = await twitter_agent._extract_post_from_element(mock_element)
        assert post is not None
        ts = datetime.fromisoformat(post['timestamp'])
        assert ts.year == 2023
        assert ts.month == 11
        assert ts.day == 20

    @pytest.mark.asyncio
    async def test_twitter_extract_post_error(self):
        agent = TwitterAgent()
        mock_element = AsyncMock()
        mock_element.query_selector.side_effect = Exception("Boom")
        
        result = await agent._extract_post_from_element(mock_element)
        assert result is None
