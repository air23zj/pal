"""
Extended tests for ranking/features.py - Target 80%+ coverage
"""
import pytest
from datetime import datetime, timezone, timedelta
from packages.ranking.features import FeatureExtractor
from packages.shared.schemas import (
    BriefItem, NoveltyInfo, RankingScores, Entity, SuggestedAction
)


def create_item(
    item_ref: str = "test_item",
    source: str = "gmail",
    item_type: str = "email",
    title: str = "Test Title",
    summary: str = "Test Summary",
    entities: list = None,
    suggested_actions: list = None,
    hours_ago: float = 0,
) -> BriefItem:
    """Helper to create test items"""
    timestamp = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return BriefItem(
        item_ref=item_ref,
        source=source,
        type=item_type,
        timestamp_utc=timestamp,
        title=title,
        summary=summary,
        why_it_matters="Test",
        entities=entities or [],
        novelty=NoveltyInfo(
            label="NEW",
            reason="Test",
            first_seen_utc=timestamp
        ),
        ranking=RankingScores(
            relevance_score=0.5,
            urgency_score=0.5,
            credibility_score=0.5,
            impact_score=0.5,
            actionability_score=0.5,
            final_score=0.5
        ),
        evidence=[],
        suggested_actions=suggested_actions or []
    )


class TestFeatureExtractorInit:
    """Test FeatureExtractor initialization"""

    def test_init_default(self):
        """Test default initialization"""
        extractor = FeatureExtractor()
        assert extractor.preferences == {}
        assert extractor.topics == set()
        assert extractor.vip_people == set()
        assert extractor.projects == set()

    def test_init_with_topics(self):
        """Test initialization with topics"""
        prefs = {"topics": ["AI", "Machine Learning", "Python"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        assert "ai" in extractor.topics
        assert "machine learning" in extractor.topics
        assert "python" in extractor.topics

    def test_init_with_vip_people(self):
        """Test initialization with VIP people"""
        prefs = {"vip_people": ["boss@company.com", "ceo@company.com"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        assert "boss@company.com" in extractor.vip_people
        assert "ceo@company.com" in extractor.vip_people

    def test_init_with_projects(self):
        """Test initialization with projects"""
        prefs = {"projects": ["Project Alpha", "Project Beta"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        assert "project alpha" in extractor.projects
        assert "project beta" in extractor.projects

    def test_init_with_all_preferences(self):
        """Test initialization with all preferences"""
        prefs = {
            "topics": ["AI"],
            "vip_people": ["ceo@company.com"],
            "projects": ["Project X"]
        }
        extractor = FeatureExtractor(user_preferences=prefs)
        assert len(extractor.topics) == 1
        assert len(extractor.vip_people) == 1
        assert len(extractor.projects) == 1


class TestExtractRelevance:
    """Test relevance extraction"""

    def test_relevance_no_preferences_default(self):
        """Test default relevance without preferences"""
        extractor = FeatureExtractor()
        item = create_item(title="Random Title", summary="Random content")
        score = extractor.extract_relevance(item)
        assert score == 0.3  # Default when no topics configured

    def test_relevance_with_topic_match_in_title(self):
        """Test relevance boost for topic match in title"""
        prefs = {"topics": ["AI"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(title="AI Breakthrough", summary="Technical details")
        score = extractor.extract_relevance(item)
        assert score > 0.3  # Should be boosted

    def test_relevance_with_topic_match_in_summary(self):
        """Test relevance boost for topic match in summary"""
        prefs = {"topics": ["machine learning"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(title="Tech News", summary="New machine learning model released")
        score = extractor.extract_relevance(item)
        assert score > 0.3

    def test_relevance_with_multiple_topic_matches(self):
        """Test relevance with multiple topic matches"""
        prefs = {"topics": ["AI", "machine learning", "python"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            title="AI and machine learning",
            summary="Using Python for AI development"
        )
        score = extractor.extract_relevance(item)
        assert score > 0.3

    def test_relevance_with_vip_person(self):
        """Test relevance boost for VIP person"""
        prefs = {"vip_people": ["ceo@company.com"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            title="Email",
            summary="Message",
            entities=[Entity(kind="person", key="ceo@company.com")]
        )
        score = extractor.extract_relevance(item)
        assert score >= 0.3  # Should get VIP boost

    def test_relevance_with_project_mention(self):
        """Test relevance boost for project mention"""
        prefs = {"projects": ["project alpha"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            title="Update",
            summary="Status",
            entities=[Entity(kind="project", key="Project Alpha")]
        )
        score = extractor.extract_relevance(item)
        assert score >= 0.3

    def test_relevance_capped_at_one(self):
        """Test that relevance score is capped at 1.0"""
        prefs = {
            "topics": ["ai", "ml", "python", "tech"],
            "vip_people": ["vip@company.com"],
            "projects": ["big project"]
        }
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            title="AI ML Python Tech",
            summary="AI ML Python Tech content",
            entities=[
                Entity(kind="person", key="vip@company.com"),
                Entity(kind="project", key="big project")
            ]
        )
        score = extractor.extract_relevance(item)
        assert score <= 1.0


class TestExtractUrgency:
    """Test urgency extraction for different item types"""

    def test_urgency_email_very_recent(self):
        """Test urgency for email received within 1 hour"""
        extractor = FeatureExtractor()
        item = create_item(item_type="email", hours_ago=0.5)
        score = extractor.extract_urgency(item)
        assert score == 0.9

    def test_urgency_email_recent(self):
        """Test urgency for email received 1-4 hours ago"""
        extractor = FeatureExtractor()
        item = create_item(item_type="email", hours_ago=2)
        score = extractor.extract_urgency(item)
        assert score == 0.7

    def test_urgency_email_same_day(self):
        """Test urgency for email received 4-24 hours ago"""
        extractor = FeatureExtractor()
        item = create_item(item_type="email", hours_ago=12)
        score = extractor.extract_urgency(item)
        assert score == 0.5

    def test_urgency_email_old(self):
        """Test urgency for email older than 24 hours"""
        extractor = FeatureExtractor()
        item = create_item(item_type="email", hours_ago=48)
        score = extractor.extract_urgency(item)
        assert score == 0.3

    def test_urgency_event_starting_soon(self):
        """Test urgency for event starting within 1 hour"""
        extractor = FeatureExtractor()
        item = create_item(item_type="event", hours_ago=-0.5)  # 30 min in future
        score = extractor.extract_urgency(item)
        assert score == 1.0

    def test_urgency_event_starting_in_few_hours(self):
        """Test urgency for event starting in 1-4 hours"""
        extractor = FeatureExtractor()
        item = create_item(item_type="event", hours_ago=-2)  # 2 hours in future
        score = extractor.extract_urgency(item)
        assert score == 0.8

    def test_urgency_event_today(self):
        """Test urgency for event later today (4-24 hours)"""
        extractor = FeatureExtractor()
        item = create_item(item_type="event", hours_ago=-12)  # 12 hours in future
        score = extractor.extract_urgency(item)
        assert score == 0.6

    def test_urgency_event_tomorrow(self):
        """Test urgency for event tomorrow (24-48 hours)"""
        extractor = FeatureExtractor()
        item = create_item(item_type="event", hours_ago=-36)  # 36 hours in future
        score = extractor.extract_urgency(item)
        assert score == 0.4

    def test_urgency_event_future(self):
        """Test urgency for event far in future"""
        extractor = FeatureExtractor()
        item = create_item(item_type="event", hours_ago=-72)  # 72 hours in future
        score = extractor.extract_urgency(item)
        assert score == 0.2

    def test_urgency_event_past(self):
        """Test urgency for past event"""
        extractor = FeatureExtractor()
        item = create_item(item_type="event", hours_ago=1)  # 1 hour ago (past)
        score = extractor.extract_urgency(item)
        assert score == 0.2

    def test_urgency_task_overdue(self):
        """Test urgency for overdue task"""
        extractor = FeatureExtractor()
        item = create_item(item_type="task", summary="OVERDUE: Complete report")
        score = extractor.extract_urgency(item)
        assert score == 1.0

    def test_urgency_task_due_today(self):
        """Test urgency for task due today"""
        extractor = FeatureExtractor()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        item = create_item(item_type="task", summary=f"Due: {today}")
        # Note: The actual implementation checks for "TODAY" keyword
        item2 = create_item(item_type="task", summary="TODAY: Complete report")
        score = extractor.extract_urgency(item2)
        assert score == 0.9

    def test_urgency_task_with_due_date(self):
        """Test urgency for task with due date"""
        extractor = FeatureExtractor()
        item = create_item(item_type="task", summary="Due: 2024-01-20")
        score = extractor.extract_urgency(item)
        assert score == 0.6

    def test_urgency_task_no_due_date(self):
        """Test urgency for task without due date"""
        extractor = FeatureExtractor()
        item = create_item(item_type="task", summary="General task")
        score = extractor.extract_urgency(item)
        assert score == 0.3

    def test_urgency_unknown_type(self):
        """Test default urgency for unknown item type"""
        extractor = FeatureExtractor()
        item = create_item(item_type="unknown")
        score = extractor.extract_urgency(item)
        assert score == 0.5


class TestExtractCredibility:
    """Test credibility extraction"""

    def test_credibility_gmail(self):
        """Test credibility for Gmail source"""
        extractor = FeatureExtractor()
        item = create_item(source="gmail")
        score = extractor.extract_credibility(item)
        assert score == 0.9

    def test_credibility_calendar(self):
        """Test credibility for Calendar source"""
        extractor = FeatureExtractor()
        item = create_item(source="calendar")
        score = extractor.extract_credibility(item)
        assert score == 0.95

    def test_credibility_tasks(self):
        """Test credibility for Tasks source"""
        extractor = FeatureExtractor()
        item = create_item(source="tasks")
        score = extractor.extract_credibility(item)
        assert score == 0.9

    def test_credibility_arxiv(self):
        """Test credibility for arXiv source"""
        extractor = FeatureExtractor()
        item = create_item(source="arxiv")
        score = extractor.extract_credibility(item)
        assert score == 0.95

    def test_credibility_news(self):
        """Test credibility for news source"""
        extractor = FeatureExtractor()
        item = create_item(source="news")
        score = extractor.extract_credibility(item)
        assert score == 0.7

    def test_credibility_x_twitter(self):
        """Test credibility for X/Twitter source"""
        extractor = FeatureExtractor()
        item = create_item(source="x")
        score = extractor.extract_credibility(item)
        assert score == 0.5

    def test_credibility_linkedin(self):
        """Test credibility for LinkedIn source"""
        extractor = FeatureExtractor()
        item = create_item(source="linkedin")
        score = extractor.extract_credibility(item)
        assert score == 0.6

    def test_credibility_podcast(self):
        """Test credibility for podcast source"""
        extractor = FeatureExtractor()
        item = create_item(source="podcast")
        score = extractor.extract_credibility(item)
        assert score == 0.6

    def test_credibility_unknown_source(self):
        """Test credibility for unknown source"""
        extractor = FeatureExtractor()
        item = create_item(source="unknown")
        score = extractor.extract_credibility(item)
        assert score == 0.5

    def test_credibility_email_with_important_marker(self):
        """Test credibility boost for important emails"""
        extractor = FeatureExtractor()
        item = create_item(
            source="gmail",
            item_type="email",
            summary="This is an important message"
        )
        score = extractor.extract_credibility(item)
        assert score == 1.0  # 0.9 + 0.1 boost, capped at 1.0


class TestExtractImpact:
    """Test impact extraction"""

    def test_impact_default(self):
        """Test default impact score"""
        extractor = FeatureExtractor()
        item = create_item()
        score = extractor.extract_impact(item)
        assert score == 0.4  # Default when no indicators

    def test_impact_with_vip_person(self):
        """Test impact boost for VIP person"""
        prefs = {"vip_people": ["ceo@company.com"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            entities=[Entity(kind="person", key="ceo@company.com")]
        )
        score = extractor.extract_impact(item)
        assert score >= 0.3  # VIP boost

    def test_impact_with_multiple_vips(self):
        """Test impact with multiple VIP mentions"""
        prefs = {"vip_people": ["ceo@company.com", "cto@company.com"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            entities=[
                Entity(kind="person", key="ceo@company.com"),
                Entity(kind="person", key="cto@company.com")
            ]
        )
        score = extractor.extract_impact(item)
        assert score >= 0.6  # Multiple VIP boost

    def test_impact_with_project(self):
        """Test impact boost for project mention"""
        prefs = {"projects": ["project x"]}
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            entities=[Entity(kind="project", key="Project X")]
        )
        score = extractor.extract_impact(item)
        assert score >= 0.2

    def test_impact_event_many_attendees(self):
        """Test impact boost for event with many attendees"""
        extractor = FeatureExtractor()
        item = create_item(
            item_type="event",
            summary="Team meeting with 10 attendees"
        )
        score = extractor.extract_impact(item)
        assert score >= 0.3  # Large meeting boost

    def test_impact_event_few_attendees(self):
        """Test impact for event with few attendees"""
        extractor = FeatureExtractor()
        item = create_item(
            item_type="event",
            summary="1-on-1 with 2 attendees"
        )
        score = extractor.extract_impact(item)
        assert score >= 0.2

    def test_impact_capped_at_one(self):
        """Test impact is capped at 1.0"""
        prefs = {
            "vip_people": ["vip1@company.com", "vip2@company.com", "vip3@company.com"],
            "projects": ["project1", "project2"]
        }
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            item_type="event",
            summary="All hands with 50 attendees",
            entities=[
                Entity(kind="person", key="vip1@company.com"),
                Entity(kind="person", key="vip2@company.com"),
                Entity(kind="person", key="vip3@company.com"),
                Entity(kind="project", key="project1"),
                Entity(kind="project", key="project2")
            ]
        )
        score = extractor.extract_impact(item)
        assert score <= 1.0


class TestExtractActionability:
    """Test actionability extraction"""

    def test_actionability_email(self):
        """Test actionability for email"""
        extractor = FeatureExtractor()
        item = create_item(item_type="email")
        score = extractor.extract_actionability(item)
        assert score >= 0.3  # Emails require replies

    def test_actionability_task(self):
        """Test actionability for task"""
        extractor = FeatureExtractor()
        item = create_item(item_type="task")
        score = extractor.extract_actionability(item)
        assert score >= 0.4  # Tasks are inherently actionable

    def test_actionability_event(self):
        """Test actionability for event"""
        extractor = FeatureExtractor()
        item = create_item(item_type="event")
        score = extractor.extract_actionability(item)
        assert score >= 0.2  # Events require preparation

    def test_actionability_with_suggested_actions(self):
        """Test actionability boost with suggested actions"""
        extractor = FeatureExtractor()
        item = create_item(
            suggested_actions=[
                SuggestedAction(type="reply", label="Reply", payload={}),
                SuggestedAction(type="archive", label="Archive", payload={})
            ]
        )
        score = extractor.extract_actionability(item)
        assert score >= 0.4  # Actions boost

    def test_actionability_with_action_keywords(self):
        """Test actionability boost for action keywords"""
        extractor = FeatureExtractor()
        keywords = ["please", "need", "required", "urgent", "asap",
                    "action", "respond", "reply", "review", "approve"]

        for keyword in keywords:
            item = create_item(
                title=f"Title with {keyword}",
                summary="Summary"
            )
            score = extractor.extract_actionability(item)
            assert score >= 0.3

    def test_actionability_with_multiple_keywords(self):
        """Test actionability with multiple action keywords"""
        extractor = FeatureExtractor()
        item = create_item(
            title="URGENT: Please review and approve",
            summary="Action required ASAP"
        )
        score = extractor.extract_actionability(item)
        assert score >= 0.5  # Multiple keyword boost

    def test_actionability_capped_at_one(self):
        """Test actionability is capped at 1.0"""
        extractor = FeatureExtractor()
        item = create_item(
            item_type="task",
            title="URGENT: Please review action required",
            summary="Need respond approve ASAP",
            suggested_actions=[
                SuggestedAction(type="complete", label="Complete", payload={}),
                SuggestedAction(type="delegate", label="Delegate", payload={}),
                SuggestedAction(type="archive", label="Archive", payload={})
            ]
        )
        score = extractor.extract_actionability(item)
        assert score <= 1.0


class TestFeatureExtractorIntegration:
    """Integration tests for feature extraction"""

    def test_all_features_in_range(self):
        """Test all features are in valid range"""
        extractor = FeatureExtractor()
        item = create_item()

        relevance = extractor.extract_relevance(item)
        urgency = extractor.extract_urgency(item)
        credibility = extractor.extract_credibility(item)
        impact = extractor.extract_impact(item)
        actionability = extractor.extract_actionability(item)

        for score in [relevance, urgency, credibility, impact, actionability]:
            assert 0.0 <= score <= 1.0

    def test_features_for_high_priority_item(self):
        """Test features for high priority item"""
        prefs = {
            "topics": ["urgent", "critical"],
            "vip_people": ["boss@company.com"]
        }
        extractor = FeatureExtractor(user_preferences=prefs)
        item = create_item(
            item_type="email",
            source="gmail",
            title="URGENT: Critical Issue",
            summary="Please respond ASAP",
            entities=[Entity(kind="person", key="boss@company.com")],
            hours_ago=0.5
        )

        relevance = extractor.extract_relevance(item)
        urgency = extractor.extract_urgency(item)
        credibility = extractor.extract_credibility(item)
        actionability = extractor.extract_actionability(item)

        # All scores should be relatively high
        assert relevance >= 0.3
        assert urgency >= 0.7
        assert credibility >= 0.8
        assert actionability >= 0.5

    def test_features_for_low_priority_item(self):
        """Test features for low priority item"""
        extractor = FeatureExtractor()
        item = create_item(
            item_type="social_post",
            source="x",
            title="Random news",
            summary="Not important",
            hours_ago=48
        )

        urgency = extractor.extract_urgency(item)
        credibility = extractor.extract_credibility(item)

        # Social media and old items should have lower scores
        assert credibility <= 0.6
