#!/usr/bin/env python3
"""
Test ranking system with sample data
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.shared.schemas import BriefItem, Entity, NoveltyInfo, RankingScores, Evidence, SuggestedAction
from packages.ranking import Ranker, rank_items, select_top_highlights


def create_sample_items() -> list[BriefItem]:
    """Create sample BriefItems for testing"""
    now = datetime.now(timezone.utc)
    
    items = [
        # Urgent meeting in 30 minutes
        BriefItem(
            item_ref="item_1",
            source="calendar",
            type="event",
            timestamp_utc=(now + timedelta(minutes=30)).isoformat(),
            title="Q4 Strategy Meeting with CEO",
            summary="Starts at 2:00 PM with 10 attendees",
            why_it_matters="pending",
            entities=[Entity(kind="person", key="ceo@company.com")],
            novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=now.isoformat()),
            ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, impact_score=0.5, actionability_score=0.5, final_score=0.5),
            evidence=[],
            suggested_actions=[],
        ),
        
        # Overdue task
        BriefItem(
            item_ref="item_2",
            source="tasks",
            type="task",
            timestamp_utc=now.isoformat(),
            title="Submit expense report",
            summary="List: Work | Due: 2024-01-15 (OVERDUE)",
            why_it_matters="pending",
            entities=[],
            novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=now.isoformat()),
            ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, impact_score=0.5, actionability_score=0.5, final_score=0.5),
            evidence=[],
            suggested_actions=[],
        ),
        
        # Important email from VIP
        BriefItem(
            item_ref="item_3",
            source="gmail",
            type="email",
            timestamp_utc=(now - timedelta(hours=2)).isoformat(),
            title="[URGENT] Please review and approve budget - from boss@company.com",
            summary="Need your approval by EOD today for Q1 budget allocation",
            why_it_matters="pending",
            entities=[Entity(kind="person", key="boss@company.com")],
            novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=now.isoformat()),
            ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, impact_score=0.5, actionability_score=0.5, final_score=0.5),
            evidence=[],
            suggested_actions=[],
        ),
        
        # Regular email
        BriefItem(
            item_ref="item_4",
            source="gmail",
            type="email",
            timestamp_utc=(now - timedelta(days=1)).isoformat(),
            title="Newsletter: Weekly tech roundup",
            summary="Latest articles and news from around the web",
            why_it_matters="pending",
            entities=[],
            novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=now.isoformat()),
            ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, impact_score=0.5, actionability_score=0.5, final_score=0.5),
            evidence=[],
            suggested_actions=[],
        ),
        
        # Future meeting
        BriefItem(
            item_ref="item_5",
            source="calendar",
            type="event",
            timestamp_utc=(now + timedelta(days=3)).isoformat(),
            title="Team lunch",
            summary="Starts at 12:00 PM with 5 attendees",
            why_it_matters="pending",
            entities=[],
            novelty=NoveltyInfo(label="NEW", reason="test", first_seen_utc=now.isoformat()),
            ranking=RankingScores(relevance_score=0.5, urgency_score=0.5, credibility_score=0.5, actionability_score=0.5, final_score=0.5),
            evidence=[],
            suggested_actions=[],
        ),
    ]
    
    return items


def main():
    """Test ranking system"""
    print("🧪 Testing Ranking System\n")
    
    # Create sample items
    items = create_sample_items()
    print(f"Created {len(items)} sample items\n")
    
    # Define user preferences
    user_preferences = {
        'topics': ['budget', 'strategy', 'Q4'],
        'vip_people': ['ceo@company.com', 'boss@company.com'],
        'projects': ['work'],
    }
    
    # Create ranker
    ranker = Ranker(user_preferences=user_preferences)
    print("Created ranker with user preferences:")
    print(f"  Topics: {user_preferences['topics']}")
    print(f"  VIPs: {user_preferences['vip_people']}")
    print(f"  Projects: {user_preferences['projects']}\n")
    
    # Rank items
    ranked = ranker.rank_items(items)
    print("📊 Ranked Items (by final_score):\n")
    
    for i, item in enumerate(ranked, 1):
        print(f"{i}. [{item.ranking.final_score:.2f}] {item.title}")
        print(f"   Source: {item.source} | Type: {item.type}")
        print(f"   Relevance: {item.ranking.relevance_score:.2f}")
        print(f"   Urgency: {item.ranking.urgency_score:.2f}")
        print(f"   Credibility: {item.ranking.credibility_score:.2f}")
        print(f"   Impact: {item.ranking.impact_score:.2f}")
        print(f"   Actionability: {item.ranking.actionability_score:.2f}")
        print()
    
    # Select top highlights
    highlights = ranker.select_top_highlights(ranked, max_count=3)
    print(f"✨ Top {len(highlights)} Highlights:\n")
    
    for i, item in enumerate(highlights, 1):
        print(f"{i}. [{item.ranking.final_score:.2f}] {item.title}")
        print()
    
    # Test caps enforcement
    print("📏 Testing Caps Enforcement:\n")
    print(f"  Max highlights: {ranker.caps.max_highlights}")
    print(f"  Max per module: {ranker.caps.max_items_per_module}")
    print(f"  Max total: {ranker.caps.max_total_items}")
    print()
    
    # Select items per module
    calendar_items = [item for item in ranked if item.source == "calendar"]
    selected_calendar = ranker.select_items_per_module(calendar_items, "calendar")
    print(f"  Calendar items: {len(calendar_items)} → selected {len(selected_calendar)}")
    
    email_items = [item for item in ranked if item.source == "gmail"]
    selected_email = ranker.select_items_per_module(email_items, "gmail")
    print(f"  Email items: {len(email_items)} → selected {len(selected_email)}")
    
    print("\n✅ Ranking system test complete!")


if __name__ == "__main__":
    main()
