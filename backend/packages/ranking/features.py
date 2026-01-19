"""
Feature extraction for importance ranking
"""
from typing import Dict, Any, List, Set, Optional
from datetime import datetime, timezone, timedelta
import re

from packages.shared.schemas import BriefItem


class FeatureExtractor:
    """
    Extracts features from BriefItems for importance scoring.
    Features are normalized to 0.0-1.0 range.
    """
    
    def __init__(self, user_preferences: Optional[Dict[str, Any]] = None):
        """
        Initialize feature extractor.
        
        Args:
            user_preferences: User-specific preferences for weighting
                - topics: List of important topics/keywords
                - vip_people: List of VIP email addresses
                - projects: List of important project names
        """
        self.preferences = user_preferences or {}
        self.topics = set(t.lower() for t in self.preferences.get('topics', []))
        self.vip_people = set(p.lower() for p in self.preferences.get('vip_people', []))
        self.projects = set(p.lower() for p in self.preferences.get('projects', []))
    
    def extract_relevance(self, item: BriefItem) -> float:
        """
        Calculate relevance score based on topic/people/project matches.
        
        Returns:
            Score 0.0-1.0 (higher = more relevant)
        """
        score = 0.0
        
        # Check topic matches in title and summary
        text = (item.title + " " + item.summary).lower()
        topic_matches = sum(1 for topic in self.topics if topic in text)
        if self.topics:
            score += min(topic_matches / len(self.topics), 0.5)
        else:
            score += 0.3  # Default relevance if no topics configured
        
        # Check VIP people mentions
        for entity in item.entities:
            if entity.kind == "person" and entity.key.lower() in self.vip_people:
                score += 0.3
                break  # Max boost for VIP
        
        # Check project mentions
        for entity in item.entities:
            if entity.kind == "project" and entity.key.lower() in self.projects:
                score += 0.2
                break
        
        return min(score, 1.0)
    
    def extract_urgency(self, item: BriefItem) -> float:
        """
        Calculate urgency score based on deadlines and time sensitivity.
        
        Returns:
            Score 0.0-1.0 (higher = more urgent)
        """
        now = datetime.now(timezone.utc)
        item_time = datetime.fromisoformat(item.timestamp_utc.replace('Z', '+00:00'))
        
        # Email urgency
        if item.type == "email":
            # Recent emails are more urgent
            age_hours = (now - item_time).total_seconds() / 3600
            if age_hours < 1:
                return 0.9
            elif age_hours < 4:
                return 0.7
            elif age_hours < 24:
                return 0.5
            else:
                return 0.3
        
        # Event urgency
        elif item.type == "event":
            # Events starting soon are urgent
            hours_until = (item_time - now).total_seconds() / 3600
            if hours_until < 0:
                return 0.2  # Past event, low urgency
            elif hours_until < 1:
                return 1.0  # Starting within 1 hour - very urgent!
            elif hours_until < 4:
                return 0.8  # Starting within 4 hours - urgent
            elif hours_until < 24:
                return 0.6  # Today - moderately urgent
            elif hours_until < 48:
                return 0.4  # Tomorrow - somewhat urgent
            else:
                return 0.2  # Future event
        
        # Task urgency
        elif item.type == "task":
            # Check for due date markers in summary
            if "OVERDUE" in item.summary:
                return 1.0
            elif "TODAY" in item.summary or "Due: " + now.strftime("%Y-%m-%d") in item.summary:
                return 0.9
            elif "Due:" in item.summary:
                return 0.6
            else:
                return 0.3  # No due date
        
        # Default urgency
        return 0.5
    
    def extract_credibility(self, item: BriefItem) -> float:
        """
        Calculate credibility score based on source trustworthiness.
        
        Returns:
            Score 0.0-1.0 (higher = more credible)
        """
        # Source credibility weights
        source_weights = {
            "gmail": 0.9,      # Emails are generally credible
            "calendar": 0.95,  # Calendar events are highly credible
            "tasks": 0.9,      # Tasks are credible
            "arxiv": 0.95,     # Academic papers are highly credible
            "news": 0.7,       # News varies in credibility
            "x": 0.5,          # Social media less credible
            "linkedin": 0.6,   # Professional network somewhat credible
            "podcast": 0.6,    # Podcasts vary
        }
        
        base_score = source_weights.get(item.source, 0.5)
        
        # Boost credibility for verified or important markers
        if item.type == "email":
            # Check for important labels or markers
            if "important" in item.summary.lower():
                base_score = min(base_score + 0.1, 1.0)
        
        return base_score
    
    def extract_impact(self, item: BriefItem) -> float:
        """
        Calculate potential impact based on entity importance.
        
        Returns:
            Score 0.0-1.0 (higher = more impactful)
        """
        score = 0.0
        
        # Check if item mentions VIP people
        vip_count = sum(
            1 for e in item.entities 
            if e.kind == "person" and e.key.lower() in self.vip_people
        )
        if vip_count > 0:
            score += min(vip_count * 0.3, 0.6)
        
        # Check if item mentions important projects
        project_count = sum(
            1 for e in item.entities 
            if e.kind == "project" and e.key.lower() in self.projects
        )
        if project_count > 0:
            score += min(project_count * 0.2, 0.4)
        
        # Boost for multiple attendees (high-impact meetings)
        if item.type == "event":
            # Look for attendee count in summary
            match = re.search(r'(\d+)\s+attendees', item.summary)
            if match:
                attendee_count = int(match.group(1))
                if attendee_count >= 5:
                    score += 0.3
                elif attendee_count >= 2:
                    score += 0.2
        
        # Default impact if no specific indicators
        if score == 0:
            score = 0.4
        
        return min(score, 1.0)
    
    def extract_actionability(self, item: BriefItem) -> float:
        """
        Calculate actionability score (can user do something about it?).
        
        Returns:
            Score 0.0-1.0 (higher = more actionable)
        """
        # Count suggested actions
        action_count = len(item.suggested_actions)
        base_score = min(action_count * 0.2, 0.6)
        
        # Boost for specific action types
        if item.type == "email":
            # Emails often require replies
            base_score += 0.3
        elif item.type == "task":
            # Tasks are inherently actionable
            base_score += 0.4
        elif item.type == "event":
            # Events require preparation
            base_score += 0.2
        
        # Check for action-oriented keywords
        text = (item.title + " " + item.summary).lower()
        action_keywords = [
            "please", "need", "required", "urgent", "asap",
            "action", "respond", "reply", "review", "approve"
        ]
        keyword_matches = sum(1 for kw in action_keywords if kw in text)
        if keyword_matches > 0:
            base_score += min(keyword_matches * 0.1, 0.3)
        
        return min(base_score, 1.0)
