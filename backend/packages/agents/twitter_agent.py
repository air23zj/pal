"""
X (Twitter) agent using browser automation.

Note: X has strict rate limits and bot detection.
This agent uses Playwright for basic scraping.
For production, consider official API or authenticated sessions.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import re
import asyncio

from .base import BrowserAgent


class TwitterAgent(BrowserAgent):
    """
    Agent for fetching posts from X (Twitter).
    
    Uses browser automation to navigate X and extract posts.
    """
    
    BASE_URL = "https://twitter.com"
    
    async def login(self, credentials: Dict[str, str]) -> bool:
        """
        Log in to X.
        
        Args:
            credentials: Dict with 'username' and 'password'
            
        Returns:
            True if login successful
            
        Note: X login is complex and may trigger 2FA.
        Consider using cookies from authenticated session instead.
        """
        if not self._page:
            raise RuntimeError("Browser not started")
        
        try:
            # Navigate to login page
            await self.navigate_to(f"{self.BASE_URL}/login")
            
            # Wait for username input
            await self._page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            await self._page.fill('input[autocomplete="username"]', credentials['username'])
            
            # Click next
            await self._page.click('text="Next"')
            
            # Wait for password input
            await self._page.wait_for_selector('input[name="password"]', timeout=10000)
            await self._page.fill('input[name="password"]', credentials['password'])
            
            # Click login
            await self._page.click('text="Log in"')
            
            # Wait for home timeline
            await self._page.wait_for_selector('[data-testid="primaryColumn"]', timeout=15000)
            
            return True
            
        except Exception as e:
            print(f"X login failed: {e}")
            return False
    
    async def fetch_feed(
        self,
        limit: int = 20,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from home timeline.
        
        Args:
            limit: Maximum number of posts
            since: Only fetch posts after this time (not fully supported)
            
        Returns:
            List of post dicts
            
        Note: Requires authenticated session.
        """
        if not self._page:
            raise RuntimeError("Browser not started")
        
        try:
            # Navigate to home
            await self.navigate_to(f"{self.BASE_URL}/home")
            
            # Wait for timeline to load
            await self._page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            
            # Scroll to load more tweets
            posts = []
            seen_ids = set()
            
            for _ in range(3):  # Scroll 3 times
                # Extract visible tweets
                tweet_elements = await self._page.query_selector_all('[data-testid="tweet"]')
                
                for element in tweet_elements:
                    if len(posts) >= limit:
                        break
                    
                    try:
                        post = await self._extract_post_from_element(element)
                        if post and post['id'] not in seen_ids:
                            seen_ids.add(post['id'])
                            posts.append(post)
                    except Exception as e:
                        print(f"Error extracting tweet from timeline: {e}")
                        continue
                
                if len(posts) >= limit:
                    break
                
                # Scroll down
                await self._page.evaluate('window.scrollBy(0, 1000)')
                await asyncio.sleep(1)
            
            return posts[:limit]
            
        except Exception as e:
            print(f"Error fetching X feed: {e}")
            return []
    
    async def fetch_user_posts(
        self,
        username: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a specific user's profile.
        
        Args:
            username: Twitter handle (without @)
            limit: Maximum number of posts
            
        Returns:
            List of post dicts
        """
        if not self._page:
            raise RuntimeError("Browser not started")
        
        # Remove @ if present
        username = username.lstrip('@')
        
        try:
            # Navigate to user profile
            await self.navigate_to(f"{self.BASE_URL}/{username}")
            
            # Wait for tweets to load
            await self._page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            
            posts = []
            seen_ids = set()
            
            for _ in range(3):  # Scroll 3 times
                tweet_elements = await self._page.query_selector_all('[data-testid="tweet"]')
                
                for element in tweet_elements:
                    if len(posts) >= limit:
                        break
                    
                    try:
                        post = await self._extract_post_from_element(element)
                        if post and post['id'] not in seen_ids:
                            seen_ids.add(post['id'])
                            posts.append(post)
                    except Exception as e:
                        print(f"Error extracting tweet from user profile: {e}")
                        continue
                
                if len(posts) >= limit:
                    break
                
                await self._page.evaluate('window.scrollBy(0, 1000)')
                await asyncio.sleep(1)
            
            return posts[:limit]
            
        except Exception as e:
            print(f"Error fetching posts from @{username}: {e}")
            return []
    
    async def _extract_post_from_element(self, element) -> Optional[Dict[str, Any]]:
        """
        Extract post data from tweet element.
        
        Args:
            element: Playwright element handle
            
        Returns:
            Post dict or None if extraction fails
        """
        try:
            # Extract text content
            text_element = await element.query_selector('[data-testid="tweetText"]')
            content = await text_element.inner_text() if text_element else ""
            
            # Extract author
            author_element = await element.query_selector('[data-testid="User-Name"]')
            author_text = await author_element.inner_text() if author_element else ""
            
            # Parse author (format: "Display Name\n@handle\n·\ntime")
            author_handle = ""
            if author_text:
                lines = author_text.split('\n')
                for line in lines:
                    if line.startswith('@'):
                        author_handle = line
                        break
            
            # Try to extract post URL to get ID
            link_element = await element.query_selector('a[href*="/status/"]')
            post_url = ""
            post_id = ""
            
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    post_url = f"{self.BASE_URL}{href}"
                    # Extract ID from URL
                    match = re.search(r'/status/(\d+)', href)
                    if match:
                        post_id = match.group(1)
            
            if not post_id:
                # Fallback: generate pseudo-ID
                post_id = f"unknown_{hash(content)}"
            
            # Extract engagement metrics
            metrics = {}
            try:
                # Replies
                reply_button = await element.query_selector('[data-testid="reply"]')
                if reply_button:
                    reply_text = await reply_button.inner_text()
                    metrics['replies'] = self._parse_metric(reply_text)
                
                # Retweets
                retweet_button = await element.query_selector('[data-testid="retweet"]')
                if retweet_button:
                    retweet_text = await retweet_button.inner_text()
                    metrics['retweets'] = self._parse_metric(retweet_text)
                
                # Likes
                like_button = await element.query_selector('[data-testid="like"]')
                if like_button:
                    like_text = await like_button.inner_text()
                    metrics['likes'] = self._parse_metric(like_text)
            except Exception as e:
                print(f"Error extracting engagement metrics: {e}")
                pass
            
            return self._format_post(
                post_id=post_id,
                author=author_handle,
                content=content,
                timestamp=datetime.now(timezone.utc),  # TODO: Parse actual timestamp
                url=post_url,
                metrics=metrics,
            )
            
        except Exception as e:
            print(f"Error extracting post: {e}")
            return None
    
    def _parse_metric(self, text: str) -> int:
        """Parse engagement metric (handles K, M suffixes)"""
        text = text.strip().upper()
        if not text or text == '':
            return 0
        
        try:
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            else:
                return int(text)
        except Exception:
            return 0
