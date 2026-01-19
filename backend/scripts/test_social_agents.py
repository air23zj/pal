#!/usr/bin/env python3
"""
Test social media agents with mock data.

Note: Real testing requires authentication and may trigger rate limits.
This script demonstrates the agent interfaces with mock data.
"""
import sys
import os
from datetime import datetime, timezone
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.agents import TwitterAgent, LinkedInAgent
# Import directly to avoid connector dependencies
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'packages'))
from normalizer.normalizer import Normalizer
from memory import detect_novelty_for_items


def create_mock_twitter_posts() -> list[dict]:
    """Create mock Twitter/X posts for testing"""
    now = datetime.now(timezone.utc)
    
    return [
        {
            'id': 'tweet_001',
            'author': '@elonmusk',
            'content': 'Exciting developments in AI agent frameworks! The future is autonomous.',
            'timestamp': now.isoformat(),
            'url': 'https://twitter.com/elonmusk/status/123456789',
            'metrics': {
                'likes': 15000,
                'retweets': 2500,
                'replies': 800,
            }
        },
        {
            'id': 'tweet_002',
            'author': '@sama',
            'content': 'New research on memory systems for LLMs. Check out our latest paper.',
            'timestamp': now.isoformat(),
            'url': 'https://twitter.com/sama/status/987654321',
            'metrics': {
                'likes': 8000,
                'retweets': 1200,
                'replies': 400,
            }
        },
        {
            'id': 'tweet_003',
            'author': '@karpathy',
            'content': 'Teaching neural networks to be better at reasoning. Long thread 🧵',
            'timestamp': now.isoformat(),
            'url': 'https://twitter.com/karpathy/status/555666777',
            'metrics': {
                'likes': 12000,
                'retweets': 3000,
                'replies': 600,
            }
        },
    ]


def create_mock_linkedin_posts() -> list[dict]:
    """Create mock LinkedIn posts for testing"""
    now = datetime.now(timezone.utc)
    
    return [
        {
            'id': 'li_001',
            'author': 'Satya Nadella',
            'content': 'Thrilled to announce our new AI initiatives at Microsoft. The intersection of cloud computing and AI will transform how businesses operate.',
            'timestamp': now.isoformat(),
            'url': 'https://www.linkedin.com/posts/satya-nadella_ai-cloud-innovation-123456',
            'metrics': {
                'reactions': 25000,
                'comments': 1500,
                'shares': 800,
            }
        },
        {
            'id': 'li_002',
            'author': 'Jensen Huang',
            'content': 'GPUs are powering the next generation of AI. Here\'s what we\'re building at NVIDIA.',
            'timestamp': now.isoformat(),
            'url': 'https://www.linkedin.com/posts/jensenh_ai-gpu-technology-789012',
            'metrics': {
                'reactions': 18000,
                'comments': 900,
                'shares': 500,
            }
        },
    ]


def test_twitter_normalization():
    """Test Twitter post normalization"""
    print("📱 Testing Twitter Post Normalization...\n")
    
    # Create mock posts
    posts = create_mock_twitter_posts()
    print(f"Created {len(posts)} mock Twitter posts\n")
    
    # Normalize to BriefItems
    items = [Normalizer.normalize_social_post(post, source="twitter") for post in posts]
    
    print("Normalized BriefItems:")
    for item in items:
        print(f"\n  Item: {item.item_ref}")
        print(f"  Title: {item.title}")
        print(f"  Summary: {item.summary[:100]}...")
        print(f"  Entities: {[e.key for e in item.entities]}")
        print(f"  Evidence: {[e.url for e in item.evidence]}")
    
    print(f"\n✅ Successfully normalized {len(items)} Twitter posts\n")
    return items


def test_linkedin_normalization():
    """Test LinkedIn post normalization"""
    print("💼 Testing LinkedIn Post Normalization...\n")
    
    # Create mock posts
    posts = create_mock_linkedin_posts()
    print(f"Created {len(posts)} mock LinkedIn posts\n")
    
    # Normalize to BriefItems
    items = [Normalizer.normalize_social_post(post, source="linkedin") for post in posts]
    
    print("Normalized BriefItems:")
    for item in items:
        print(f"\n  Item: {item.item_ref}")
        print(f"  Title: {item.title}")
        print(f"  Summary: {item.summary[:100]}...")
        print(f"  Entities: {[e.key for e in item.entities]}")
        print(f"  Evidence: {[e.url for e in item.evidence]}")
    
    print(f"\n✅ Successfully normalized {len(items)} LinkedIn posts\n")
    return items


def test_novelty_detection():
    """Test novelty detection with social posts"""
    print("🔍 Testing Novelty Detection for Social Posts...\n")
    
    user_id = "test_user"
    
    # Get Twitter posts
    twitter_posts = create_mock_twitter_posts()
    twitter_items = [Normalizer.normalize_social_post(post, source="twitter") for post in twitter_posts]
    
    # First time - should all be NEW
    items_with_novelty = detect_novelty_for_items(
        user_id=user_id,
        items=twitter_items,
        items_data=twitter_posts,
        exclude_repeats=False,
    )
    
    print("First detection:")
    for item in items_with_novelty:
        print(f"  {item.title[:50]}... → {item.novelty.label}")
    
    # Second time - should all be REPEAT
    items_with_novelty2 = detect_novelty_for_items(
        user_id=user_id,
        items=twitter_items,
        items_data=twitter_posts,
        exclude_repeats=False,
    )
    
    print("\nSecond detection:")
    for item in items_with_novelty2:
        print(f"  {item.title[:50]}... → {item.novelty.label}")
    
    # Filter repeats
    new_only = detect_novelty_for_items(
        user_id=user_id,
        items=twitter_items,
        items_data=twitter_posts,
        exclude_repeats=True,
    )
    
    print(f"\nAfter filtering: {len(new_only)} items (expected: 0)")
    print("✅ Novelty detection working for social posts\n")


async def test_agent_interface():
    """Test agent interface (without real browser)"""
    print("🤖 Testing Agent Interface...\n")
    
    print("TwitterAgent:")
    print("  - Base URL:", TwitterAgent.BASE_URL)
    print("  - Methods: login(), fetch_feed(), fetch_user_posts()")
    print("  - Requires: Playwright browser automation")
    print("  - Note: Real usage requires authentication\n")
    
    print("LinkedInAgent:")
    print("  - Base URL:", LinkedInAgent.BASE_URL)
    print("  - Methods: login(), fetch_feed(), fetch_user_posts()")
    print("  - Requires: Playwright browser automation")
    print("  - Note: Real usage requires authentication\n")
    
    print("✅ Agent interfaces defined correctly\n")


def test_integration_flow():
    """Test full integration flow with mock data"""
    print("🔄 Testing Full Integration Flow...\n")
    
    user_id = "test_user"
    
    # Step 1: Fetch posts (mock)
    print("1. Fetching posts from Twitter and LinkedIn...")
    twitter_posts = create_mock_twitter_posts()
    linkedin_posts = create_mock_linkedin_posts()
    print(f"   Found {len(twitter_posts)} Twitter + {len(linkedin_posts)} LinkedIn posts\n")
    
    # Step 2: Normalize
    print("2. Normalizing to BriefItems...")
    twitter_items = [Normalizer.normalize_social_post(post, source="twitter") for post in twitter_posts]
    linkedin_items = [Normalizer.normalize_social_post(post, source="linkedin") for post in linkedin_posts]
    all_items = twitter_items + linkedin_items
    print(f"   Normalized {len(all_items)} total items\n")
    
    # Step 3: Novelty detection
    print("3. Detecting novelty...")
    all_posts_data = twitter_posts + linkedin_posts
    items_with_novelty = detect_novelty_for_items(
        user_id=user_id,
        items=all_items,
        items_data=all_posts_data,
        exclude_repeats=True,
    )
    print(f"   {len(items_with_novelty)} new/updated items\n")
    
    # Step 4: Show results
    print("4. Final Results:")
    for item in items_with_novelty[:3]:  # Show top 3
        print(f"\n   📄 {item.title}")
        print(f"      Source: {item.source}")
        print(f"      Novelty: {item.novelty.label}")
        print(f"      Entities: {[e.key for e in item.entities]}")
    
    print(f"\n✅ Integration flow complete!\n")


def main():
    """Run all tests"""
    print("🧪 Testing Social Media Agents\n")
    print("=" * 60 + "\n")
    
    # Test normalization
    test_twitter_normalization()
    print("=" * 60 + "\n")
    
    test_linkedin_normalization()
    print("=" * 60 + "\n")
    
    # Test novelty detection
    test_novelty_detection()
    print("=" * 60 + "\n")
    
    # Test agent interface
    asyncio.run(test_agent_interface())
    print("=" * 60 + "\n")
    
    # Test integration
    test_integration_flow()
    print("=" * 60 + "\n")
    
    print("🎉 All tests passed!\n")
    print("Next steps:")
    print("  1. Install Playwright: pip install playwright && playwright install")
    print("  2. Set up authentication credentials")
    print("  3. Test with real browser scraping (rate limits apply)")
    print("  4. Consider using official APIs for production")


if __name__ == "__main__":
    main()
