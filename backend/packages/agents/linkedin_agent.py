"""
LinkedIn agent using browser automation.

Note: LinkedIn has strict scraping policies and bot detection.
This agent uses Playwright for basic scraping.
For production, consider official LinkedIn API.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import re
import asyncio

from .base import BrowserAgent


class LinkedInAgent(BrowserAgent):
    """
    Agent for fetching posts from LinkedIn.
    
    Uses browser automation to navigate LinkedIn and extract posts.
    """
    
    BASE_URL = "https://www.linkedin.com"
    
    async def login(self, credentials: Dict[str, str]) -> bool:
        """
        Log in to LinkedIn.
        
        Args:
            credentials: Dict with 'email' and 'password'
            
        Returns:
            True if login successful
            
        Note: LinkedIn may trigger CAPTCHA or email verification.
        Consider using cookies from authenticated session.
        """
        if not self._page:
            raise RuntimeError("Browser not started")
        
        try:
            # Navigate to login page
            await self.navigate_to(f"{self.BASE_URL}/login")
            
            # Fill email
            await self._page.wait_for_selector('#username', timeout=10000)
            await self._page.fill('#username', credentials['email'])
            
            # Fill password
            await self._page.fill('#password', credentials['password'])
            
            # Click sign in
            await self._page.click('button[type="submit"]')
            
            # Wait for feed to load
            await self._page.wait_for_selector('.scaffold-layout__main', timeout=15000)
            
            return True
            
        except Exception as e:
            print(f"LinkedIn login failed: {e}")
            return False
    
    async def fetch_feed(
        self,
        limit: int = 20,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from LinkedIn feed.
        
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
            # Navigate to feed
            await self.navigate_to(f"{self.BASE_URL}/feed/")
            
            # Wait for posts to load
            await self._page.wait_for_selector('.feed-shared-update-v2', timeout=10000)
            
            posts = []
            seen_ids = set()
            
            for _ in range(3):  # Scroll 3 times
                # Extract visible posts
                post_elements = await self._page.query_selector_all('.feed-shared-update-v2')
                
                for element in post_elements:
                    if len(posts) >= limit:
                        break
                    
                    try:
                        post = await self._extract_post_from_element(element)
                        if post and post['id'] not in seen_ids:
                            seen_ids.add(post['id'])
                            posts.append(post)
                    except Exception as e:
                        print(f"Error extracting post from feed: {e}")
                        continue
                
                if len(posts) >= limit:
                    break
                
                # Scroll down
                await self._page.evaluate('window.scrollBy(0, 1000)')
                await asyncio.sleep(2)  # LinkedIn loads slower
            
            return posts[:limit]
            
        except Exception as e:
            print(f"Error fetching LinkedIn feed: {e}")
            return []
    
    async def fetch_user_posts(
        self,
        username: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a specific user's profile.
        
        Args:
            username: LinkedIn username or profile ID
            limit: Maximum number of posts
            
        Returns:
            List of post dicts
        """
        if not self._page:
            raise RuntimeError("Browser not started")
        
        try:
            # Navigate to user's recent activity
            # LinkedIn profile URLs: /in/{username}/ or /in/{username}/recent-activity/
            profile_url = f"{self.BASE_URL}/in/{username}/recent-activity/all/"
            await self.navigate_to(profile_url)
            
            # Wait for posts to load
            await self._page.wait_for_selector('.feed-shared-update-v2', timeout=10000)
            
            posts = []
            seen_ids = set()
            
            for _ in range(3):
                post_elements = await self._page.query_selector_all('.feed-shared-update-v2')
                
                for element in post_elements:
                    if len(posts) >= limit:
                        break
                    
                    try:
                        post = await self._extract_post_from_element(element)
                        if post and post['id'] not in seen_ids:
                            seen_ids.add(post['id'])
                            posts.append(post)
                    except Exception as e:
                        print(f"Error extracting post from user profile: {e}")
                        continue
                
                if len(posts) >= limit:
                    break
                
                await self._page.evaluate('window.scrollBy(0, 1000)')
                await asyncio.sleep(2)
            
            return posts[:limit]
            
        except Exception as e:
            print(f"Error fetching posts from {username}: {e}")
            return []
    
    async def _extract_post_from_element(self, element) -> Optional[Dict[str, Any]]:
        """
        Extract post data from LinkedIn post element.
        
        Args:
            element: Playwright element handle
            
        Returns:
            Post dict or None if extraction fails
        """
        try:
            # Extract post ID from data attribute
            post_id = await element.get_attribute('data-urn')
            if not post_id:
                # Fallback: use element ID
                post_id = await element.get_attribute('id')
            if not post_id:
                post_id = f"unknown_{hash(await element.inner_html())}"
            
            # Extract author name
            author_element = await element.query_selector('.update-components-actor__name')
            author = await author_element.inner_text() if author_element else "Unknown"
            
            # Extract post content
            # LinkedIn uses different classes for different content types
            content_element = await element.query_selector('.feed-shared-update-v2__description')
            content = ""
            
            if content_element:
                # Try to get the main text span
                text_span = await content_element.query_selector('.break-words')
                if text_span:
                    content = await text_span.inner_text()
                else:
                    content = await content_element.inner_text()
            
            # Clean up content (remove "see more" buttons, etc.)
            content = content.strip()
            if '…see more' in content:
                content = content.replace('…see more', '').strip()
            
            # Extract post URL
            permalink_element = await element.query_selector('a.app-aware-link')
            post_url = ""
            if permalink_element:
                href = await permalink_element.get_attribute('href')
                if href and '/posts/' in href:
                    post_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
            
            # Extract engagement metrics
            metrics = {}
            try:
                # Reactions count
                reactions_element = await element.query_selector('.social-details-social-counts__reactions-count')
                if reactions_element:
                    reactions_text = await reactions_element.inner_text()
                    metrics['reactions'] = self._parse_metric(reactions_text)
                
                # Comments count
                comments_element = await element.query_selector('.social-details-social-counts__comments')
                if comments_element:
                    comments_text = await comments_element.inner_text()
                    # Text format: "X comments"
                    metrics['comments'] = self._parse_metric(comments_text.split()[0])
                
                # Shares/reposts
                shares_element = await element.query_selector('.social-details-social-counts__item--with-social-proof')
                if shares_element:
                    shares_text = await shares_element.inner_text()
                    metrics['shares'] = self._parse_metric(shares_text)
            except Exception as e:
                print(f"Error extracting metrics: {e}")
                pass
            
            # Extract timestamp
            time_element = await element.query_selector('.update-components-actor__sub-description time')
            timestamp = datetime.now(timezone.utc)  # Default to now
            
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    try:
                        timestamp = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except Exception as e:
                        print(f"Error parsing timestamp: {e}")
                        pass
            
            return self._format_post(
                post_id=post_id,
                author=author,
                content=content,
                timestamp=timestamp,
                url=post_url,
                metrics=metrics,
            )
            
        except Exception as e:
            print(f"Error extracting LinkedIn post: {e}")
            return None
    
    def _parse_metric(self, text: str) -> int:
        """Parse engagement metric (handles K, M suffixes and commas)"""
        text = text.strip().upper().replace(',', '')
        if not text or text == '':
            return 0
        
        # Extract first number-like token
        import re
        match = re.search(r'[\d.]+[KM]?', text)
        if not match:
            return 0
        
        num_str = match.group()
        
        try:
            if 'K' in num_str:
                return int(float(num_str.replace('K', '')) * 1000)
            elif 'M' in num_str:
                return int(float(num_str.replace('M', '')) * 1000000)
            else:
                return int(float(num_str))
        except Exception:
            return 0
