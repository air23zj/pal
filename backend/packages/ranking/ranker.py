"""
Ranking engine for importance scoring and item selection
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from packages.shared.schemas import BriefItem, RankingScores
from .features import FeatureExtractor


@dataclass
class RankingWeights:
    """Weights for ranking formula components"""
    relevance: float = 0.45
    urgency: float = 0.20
    credibility: float = 0.15
    impact: float = 0.10
    actionability: float = 0.10
    
    def normalize(self) -> 'RankingWeights':
        """Ensure weights sum to 1.0"""
        total = self.relevance + self.urgency + self.credibility + self.impact + self.actionability
        return RankingWeights(
            relevance=self.relevance / total,
            urgency=self.urgency / total,
            credibility=self.credibility / total,
            impact=self.impact / total,
            actionability=self.actionability / total,
        )


@dataclass
class SelectionCaps:
    """Budget constraints for item selection"""
    max_highlights: int = 5
    max_items_per_module: int = 8
    default_items_per_module: int = 3
    max_total_items: int = 30


class Ranker:
    """
    Ranks BriefItems by importance using a weighted scoring algorithm.
    
    Formula:
        final_score = 
            w1 * relevance +
            w2 * urgency +
            w3 * credibility +
            w4 * impact +
            w5 * actionability
    """
    
    def __init__(
        self,
        user_preferences: Optional[Dict[str, Any]] = None,
        weights: Optional[RankingWeights] = None,
        caps: Optional[SelectionCaps] = None,
    ):
        """
        Initialize ranker.
        
        Args:
            user_preferences: User-specific preferences for feature extraction
            weights: Custom ranking weights (default: per spec)
            caps: Selection caps/budgets (default: per spec)
        """
        self.feature_extractor = FeatureExtractor(user_preferences)
        self.weights = (weights or RankingWeights()).normalize()
        self.caps = caps or SelectionCaps()
    
    def score_item(self, item: BriefItem) -> RankingScores:
        """
        Calculate all ranking scores for an item.
        
        Args:
            item: BriefItem to score
            
        Returns:
            RankingScores with all component scores and final score
        """
        # Extract feature scores
        relevance = self.feature_extractor.extract_relevance(item)
        urgency = self.feature_extractor.extract_urgency(item)
        credibility = self.feature_extractor.extract_credibility(item)
        impact = self.feature_extractor.extract_impact(item)
        actionability = self.feature_extractor.extract_actionability(item)
        
        # Calculate final weighted score
        final_score = (
            self.weights.relevance * relevance +
            self.weights.urgency * urgency +
            self.weights.credibility * credibility +
            self.weights.impact * impact +
            self.weights.actionability * actionability
        )
        
        return RankingScores(
            relevance_score=relevance,
            urgency_score=urgency,
            credibility_score=credibility,
            actionability_score=actionability,
            final_score=final_score,
        )
    
    def rank_items(self, items: List[BriefItem]) -> List[BriefItem]:
        """
        Score and rank a list of items.
        
        Args:
            items: List of BriefItems to rank
            
        Returns:
            List of items sorted by final_score (highest first)
        """
        # Score each item
        for item in items:
            item.ranking = self.score_item(item)
        
        # Sort by final score (descending)
        ranked = sorted(items, key=lambda x: x.ranking.final_score, reverse=True)
        
        return ranked
    
    def select_top_highlights(
        self,
        items: List[BriefItem],
        max_count: Optional[int] = None,
    ) -> List[BriefItem]:
        """
        Select top highlights from ranked items.
        
        Args:
            items: Ranked list of BriefItems
            max_count: Maximum number of highlights (default: from caps)
            
        Returns:
            Top N items as highlights
        """
        max_count = max_count or self.caps.max_highlights
        
        # Rank if not already ranked
        if not items or not items[0].ranking:
            items = self.rank_items(items)
        
        # Select top items
        highlights = items[:max_count]
        
        return highlights
    
    def select_items_per_module(
        self,
        items: List[BriefItem],
        module_name: str,
        max_count: Optional[int] = None,
    ) -> List[BriefItem]:
        """
        Select items for a specific module with cap enforcement.
        
        Args:
            items: Ranked list of BriefItems for this module
            module_name: Name of the module
            max_count: Maximum items for this module (default: from caps)
            
        Returns:
            Selected items for this module
        """
        max_count = max_count or self.caps.max_items_per_module
        
        # Rank if not already ranked
        if not items or not items[0].ranking:
            items = self.rank_items(items)
        
        # Select top items up to cap
        selected = items[:max_count]
        
        return selected
    
    def enforce_total_cap(
        self,
        all_items: List[BriefItem],
        max_total: Optional[int] = None,
    ) -> List[BriefItem]:
        """
        Enforce total item count cap across all modules.
        
        Args:
            all_items: All items from all modules (already ranked)
            max_total: Maximum total items (default: from caps)
            
        Returns:
            Items selected to fit within total cap
        """
        max_total = max_total or self.caps.max_total_items
        
        # Re-rank all items together if needed
        if not all_items or not all_items[0].ranking:
            all_items = self.rank_items(all_items)
        else:
            # Just resort by score
            all_items = sorted(all_items, key=lambda x: x.ranking.final_score, reverse=True)
        
        # Apply total cap
        return all_items[:max_total]
    
    def adjust_weights_from_feedback(
        self,
        feedback_events: List[Dict[str, Any]]
    ) -> RankingWeights:
        """
        Adjust ranking weights based on user feedback.
        
        Args:
            feedback_events: List of feedback events (thumb_up/down, etc.)
            
        Returns:
            Adjusted weights
        """
        # TODO: Implement learning from feedback
        # For now, return current weights
        # Future: use ML to learn optimal weights
        
        # Count positive vs negative feedback
        positive = sum(1 for e in feedback_events if e.get('event_type') == 'thumb_up')
        negative = sum(1 for e in feedback_events if e.get('event_type') == 'thumb_down')
        
        # Simple adjustment: boost urgency if user responds to urgent items
        if positive > negative * 2:
            # User likes current ranking
            return self.weights
        elif negative > positive:
            # User dislikes current ranking - adjust slightly
            return RankingWeights(
                relevance=self.weights.relevance + 0.05,
                urgency=self.weights.urgency - 0.05,
                credibility=self.weights.credibility,
                impact=self.weights.impact,
                actionability=self.weights.actionability,
            ).normalize()
        
        return self.weights


def rank_items(
    items: List[BriefItem],
    user_preferences: Optional[Dict[str, Any]] = None,
    weights: Optional[RankingWeights] = None,
) -> List[BriefItem]:
    """
    Convenience function to rank items.
    
    Args:
        items: List of BriefItems to rank
        user_preferences: User preferences for personalization
        weights: Custom ranking weights
        
    Returns:
        Ranked list of items
    """
    ranker = Ranker(user_preferences=user_preferences, weights=weights)
    return ranker.rank_items(items)


def select_top_highlights(
    items: List[BriefItem],
    max_count: int = 5,
    user_preferences: Optional[Dict[str, Any]] = None,
) -> List[BriefItem]:
    """
    Convenience function to select top highlights.
    
    Args:
        items: List of BriefItems
        max_count: Maximum highlights to select
        user_preferences: User preferences for personalization
        
    Returns:
        Top highlights
    """
    ranker = Ranker(user_preferences=user_preferences)
    ranked = ranker.rank_items(items)
    return ranked[:max_count]
