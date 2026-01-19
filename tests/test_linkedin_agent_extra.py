"""
Extra tests for LinkedIn agent to achieve 90%+ coverage.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import asyncio

from packages.agents.linkedin_agent import LinkedInAgent

class TestLinkedInAgentExtra:
    """Extra tests for LinkedInAgent"""

    @pytest.mark.asyncio
    async def test_linkedin_fetch_user_posts_limit_and_paging(self):
        """Test paging and limit reaching in fetch_user_posts"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        # Mock unique elements
        mock_elements = [AsyncMock() for _ in range(5)]
        agent._page.query_selector_all.return_value = mock_elements
        
        # Mock extraction with unique IDs
        extract_count = 0
        async def mock_extract(e):
            nonlocal extract_count
            extract_count += 1
            return {"id": f"id_{extract_count}", "content": "test"}
            
        with patch.object(agent, '_extract_post_from_element', side_effect=mock_extract):
            # Fetch with small limit
            posts = await agent.fetch_user_posts("testuser", limit=2)
            assert len(posts) == 2
            # Should have called extract exactly 2 times due to break
            assert extract_count == 2

    @pytest.mark.asyncio
    async def test_linkedin_fetch_user_posts_extraction_error(self):
        """Test handling of extraction errors during fetch"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        mock_elem = AsyncMock()
        agent._page.query_selector_all.return_value = [mock_elem]
        
        with patch.object(agent, '_extract_post_from_element', side_effect=Exception("Failed")):
            posts = await agent.fetch_user_posts("testuser")
            assert posts == []

    @pytest.mark.asyncio
    async def test_linkedin_extract_post_complex_scenarios(self):
        """Test extraction with various element structures (break-words, see more, metrics)"""
        agent = LinkedInAgent()
        element = AsyncMock()
        
        # 1. Fallback ID (no data-urn, use id)
        element.get_attribute.side_effect = lambda attr: "elem_id" if attr == "id" else None
        
        # 2. Content with .break-words and 'see more'
        content_elem = AsyncMock()
        text_span = AsyncMock()
        text_span.inner_text.return_value = "Main content…see more"
        content_elem.query_selector.return_value = text_span
        
        # 3. Attributes and children
        def mock_query_selector(selector):
            if '.feed-shared-update-v2__description' in selector:
                return content_elem
            if '.update-components-actor__name' in selector:
                m = AsyncMock()
                m.inner_text.return_value = "Author Name"
                return m
            if 'a.app-aware-link' in selector:
                m = AsyncMock()
                m.get_attribute.return_value = "/posts/123"
                return m
            if '.social-details-social-counts__reactions-count' in selector:
                m = AsyncMock()
                m.inner_text.return_value = "1.2K"
                return m
            if '.social-details-social-counts__comments' in selector:
                m = AsyncMock()
                m.inner_text.return_value = "50 comments"
                return m
            if '.social-details-social-counts__item--with-social-proof' in selector:
                m = AsyncMock()
                m.inner_text.return_value = "10 shares"
                return m
            if '.update-components-actor__sub-description time' in selector:
                m = AsyncMock()
                m.get_attribute.return_value = "2024-01-01T12:00:00Z"
                return m
            return None

        element.query_selector.side_effect = mock_query_selector
        
        post = await agent._extract_post_from_element(element)
        
        assert post['id'] == "elem_id"
        assert post['author'] == "Author Name"
        assert post['content'] == "Main content"
        assert post['url'] == "https://www.linkedin.com/posts/123"
        assert post['metrics']['reactions'] == 1200
        assert post['metrics']['comments'] == 50
        assert post['metrics']['shares'] == 10
        assert "2024-01-01" in post['timestamp']

    @pytest.mark.asyncio
    async def test_linkedin_extract_post_hashed_id(self):
        """Test fallback to hashed ID when no ID attributes present"""
        agent = LinkedInAgent()
        element = AsyncMock()
        element.get_attribute.return_value = None
        element.inner_html.return_value = "<div>unique content</div>"
        
        # Minimize other calls
        element.query_selector.return_value = None
        
        post = await agent._extract_post_from_element(element)
        assert post['id'].startswith("unknown_")

    @pytest.mark.asyncio
    async def test_linkedin_extract_post_url_variants(self):
        """Test absolute and invalid URL extraction"""
        agent = LinkedInAgent()
        element = AsyncMock()
        element.get_attribute.return_value = "id1"
        
        mock_link = AsyncMock()
        mock_link.get_attribute.side_effect = [
            "https://external.com/posts/1", # absolute
            "/not-a-post/2"                 # invalid
        ]
        
        def mock_query(selector):
            if 'a.app-aware-link' in selector: return mock_link
            return None
        element.query_selector.side_effect = mock_query
        
        # Call 1: Absolute URL
        post1 = await agent._extract_post_from_element(element)
        assert post1['url'] == "https://external.com/posts/1"
        
        # Call 2: Invalid URL (no /posts/)
        post2 = await agent._extract_post_from_element(element)
        assert post2['url'] == ""

    @pytest.mark.asyncio
    async def test_linkedin_extract_post_metrics_error_handling(self):
        """Test error handling within metrics extraction"""
        agent = LinkedInAgent()
        element = AsyncMock()
        element.get_attribute.return_value = "id1"
        
        # Mock a reaction element that fails on inner_text
        mock_reactions = AsyncMock()
        mock_reactions.inner_text.side_effect = Exception("Metric fail")
        
        def mock_query(selector):
            if '.social-details-social-counts__reactions-count' in selector:
                return mock_reactions
            return None
        element.query_selector.side_effect = mock_query
        
        # Should not raise exception
        post = await agent._extract_post_from_element(element)
        assert post is not None
        assert 'reactions' not in post['metrics']

    @pytest.mark.asyncio
    async def test_linkedin_extract_post_timestamp_parsing_error(self):
        """Test handling of malformed timestamps"""
        agent = LinkedInAgent()
        element = AsyncMock()
        element.get_attribute.return_value = "id1"
        
        mock_time = AsyncMock()
        mock_time.get_attribute.return_value = "invalid-date"
        
        def mock_query(selector):
            if '.update-components-actor__sub-description time' in selector:
                return mock_time
            return None
        element.query_selector.side_effect = mock_query
        
        # Should use default timestamp (now)
        post = await agent._extract_post_from_element(element)
        assert post is not None
        assert post['timestamp'] is not None

    @pytest.mark.asyncio
    async def test_linkedin_login_success(self):
        """Test successful LinkedIn login flow"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        
        # Fill/Click should work
        agent._page.fill = AsyncMock()
        agent._page.click = AsyncMock()
        agent._page.wait_for_selector = AsyncMock()
        
        result = await agent.login({'email': 'test@example.com', 'password': 'pass'})
        assert result is True
        assert agent._page.fill.call_count == 2
        agent._page.click.assert_called_with('button[type="submit"]')

    @pytest.mark.asyncio
    async def test_linkedin_fetch_feed_logic(self):
        """Test fetch_feed paging and scrolling"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        mock_elem = AsyncMock()
        agent._page.query_selector_all.return_value = [mock_elem]
        
        with patch.object(agent, '_extract_post_from_element', AsyncMock(return_value={"id": "f1", "content": "c"})):
            posts = await agent.fetch_feed(limit=5)
            assert len(posts) == 1
            assert agent._page.evaluate.called # Scrolled

    @pytest.mark.asyncio
    async def test_linkedin_extract_post_base_branch(self):
        """Test some specific base branches in extraction"""
        agent = LinkedInAgent()
        element = AsyncMock()
        element.get_attribute.return_value = "urn:123"
        
        # Content element without text span
        content_elem = AsyncMock()
        content_elem.query_selector.return_value = None
        content_elem.inner_text.return_value = "Direct text"
        
        def mock_query(selector):
            if '.feed-shared-update-v2__description' in selector: return content_elem
            return None
        element.query_selector.side_effect = mock_query
        
        post = await agent._extract_post_from_element(element)
        assert post['content'] == "Direct text"

    @pytest.mark.asyncio
    async def test_linkedin_extract_post_general_error(self):
        """Test general error block in extract_post_from_element"""
        agent = LinkedInAgent()
        element = AsyncMock()
        element.get_attribute.side_effect = Exception("Major fail")
        
        post = await agent._extract_post_from_element(element)
        assert post is None

    @pytest.mark.asyncio
    async def test_linkedin_fetch_feed_general_error(self):
        """Test general error block in fetch_feed"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector.side_effect = Exception("Wait fail")
        
        posts = await agent.fetch_feed()
        assert posts == []

    @pytest.mark.asyncio
    async def test_linkedin_fetch_user_posts_general_error(self):
        """Test general error block in fetch_user_posts"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        agent._page.wait_for_selector.side_effect = Exception("Wait fail")
        
        posts = await agent.fetch_user_posts("user")
        assert posts == []

    def test_linkedin_parse_metric_exception(self):
        """Test exception handling in _parse_metric"""
        agent = LinkedInAgent()
        # This will match the regex but fail float() conversion
        assert agent._parse_metric("1.2.3K") == 0

    def test_linkedin_parse_metric_empty(self):
        """Test empty/none metric text"""
        agent = LinkedInAgent()
        assert agent._parse_metric("") == 0
        assert agent._parse_metric("   ") == 0

    @pytest.mark.asyncio
    async def test_linkedin_fetch_feed_limit_and_error(self):
        """Test limit break and extraction error in fetch_feed"""
        agent = LinkedInAgent()
        agent._page = AsyncMock()
        mock_elements = [AsyncMock() for _ in range(5)]
        agent._page.query_selector_all.return_value = mock_elements
        
        # Call 1: Limit reached
        with patch.object(agent, '_extract_post_from_element', AsyncMock(side_effect=lambda e: {"id": str(id(e))})) as mock_ext:
            posts = await agent.fetch_feed(limit=2)
            assert len(posts) == 2
            assert mock_ext.call_count == 2
            
        # Call 2: Extraction error handled
        with patch.object(agent, '_extract_post_from_element', side_effect=Exception("Loop fail")):
            posts = await agent.fetch_feed()
            assert posts == []
