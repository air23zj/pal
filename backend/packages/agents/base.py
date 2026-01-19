"""
Base class for browser-based agents.

Uses browser-use for autonomous browser interaction.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timezone


class BrowserAgent(ABC):
    """
    Base class for browser-based social media agents.
    
    Subclasses implement specific platforms (Twitter, LinkedIn, etc.)
    """
    
    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
    ):
        """
        Initialize browser agent.
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self._browser = None
        self._context = None
        self._page = None
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.stop()
    
    async def start(self):
        """
        Start browser instance.
        
        Uses Playwright to launch browser.
        """
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            
        except ImportError:
            raise RuntimeError(
                "Playwright not installed. Run: pip install playwright && playwright install"
            )
    
    async def stop(self):
        """Stop browser instance"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()
    
    @abstractmethod
    async def login(self, credentials: Dict[str, str]) -> bool:
        """
        Log in to the platform.
        
        Args:
            credentials: Login credentials (username, password, etc.)
            
        Returns:
            True if login successful
        """
        pass
    
    @abstractmethod
    async def fetch_feed(
        self,
        limit: int = 20,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from feed.
        
        Args:
            limit: Maximum number of posts to fetch
            since: Only fetch posts after this time
            
        Returns:
            List of post dicts
        """
        pass
    
    @abstractmethod
    async def fetch_user_posts(
        self,
        username: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a specific user.
        
        Args:
            username: Username to fetch from
            limit: Maximum number of posts
            
        Returns:
            List of post dicts
        """
        pass
    
    async def navigate_to(self, url: str):
        """Navigate to URL"""
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")
        await self._page.goto(url, timeout=self.timeout)
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        """Wait for element to appear"""
        if not self._page:
            raise RuntimeError("Browser not started")
        await self._page.wait_for_selector(
            selector,
            timeout=timeout or self.timeout
        )
    
    async def extract_text(self, selector: str) -> str:
        """Extract text from element"""
        if not self._page:
            raise RuntimeError("Browser not started")
        element = await self._page.query_selector(selector)
        if element:
            return await element.inner_text()
        return ""
    
    async def extract_all_text(self, selector: str) -> List[str]:
        """Extract text from all matching elements"""
        if not self._page:
            raise RuntimeError("Browser not started")
        elements = await self._page.query_selector_all(selector)
        texts = []
        for element in elements:
            text = await element.inner_text()
            texts.append(text)
        return texts
    
    async def screenshot(self, path: str):
        """Take screenshot"""
        if not self._page:
            raise RuntimeError("Browser not started")
        await self._page.screenshot(path=path)
    
    def _format_post(
        self,
        post_id: str,
        author: str,
        content: str,
        timestamp: Optional[datetime] = None,
        url: Optional[str] = None,
        metrics: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Format post data into standard structure.
        
        Args:
            post_id: Post identifier
            author: Author username/handle
            content: Post text content
            timestamp: Post timestamp
            url: URL to post
            metrics: Engagement metrics (likes, shares, etc.)
            
        Returns:
            Standardized post dict
        """
        return {
            'id': post_id,
            'author': author,
            'content': content,
            'timestamp': timestamp.isoformat() if timestamp else None,
            'url': url,
            'metrics': metrics or {},
            'fetched_at': datetime.now(timezone.utc).isoformat(),
        }
