"""
Active Learning Integration

Integrates predictive models with the ranking pipeline:
- Identifies uncertain predictions for learning
- Balances exploration (learning) vs exploitation (accuracy)
- Tracks learning progress and model improvement
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from packages.shared.schemas import BriefItem
from packages.ranking.predictive_model import (
    get_predictive_model,
    get_active_learning_manager,
    PredictionResult
)
from packages.ranking.features import FeatureExtractor


@dataclass
class LearningItem:
    """Item selected for active learning"""

    item: BriefItem
    prediction: PredictionResult
    learning_priority: float  # 0-1, higher = better for learning
    reason: str  # Why this item was selected for learning


@dataclass
class ActiveLearningConfig:
    """Configuration for active learning"""

    enabled: bool = True
    learning_budget: int = 3  # Max items per brief for learning
    uncertainty_threshold: float = 0.6  # Below this = uncertain
    exploration_rate: float = 0.2  # Fraction of items for exploration
    min_samples_before_learning: int = 20  # Don't learn until this many samples


class ActiveLearningIntegrator:
    """
    Integrates active learning into the ranking pipeline

    Strategy:
    1. Use predictive model for initial ranking
    2. Identify high-uncertainty items for learning
    3. Include learning items in final selection
    4. Track feedback to improve model over time
    """

    def __init__(self, user_id: str, config: Optional[ActiveLearningConfig] = None):
        """
        Initialize active learning integrator

        Args:
            user_id: User ID
            config: Active learning configuration
        """
        self.user_id = user_id
        self.config = config or ActiveLearningConfig()

        # Get ML components
        self.predictive_model = get_predictive_model(user_id)
        self.active_learning = get_active_learning_manager(user_id)
        self.feature_extractor = FeatureExtractor()

        # Learning session tracking
        self.current_session_learning_items: List[LearningItem] = []

    def enhance_ranking_with_predictions(
        self, items: List[BriefItem]
    ) -> List[BriefItem]:
        """
        Enhance item ranking with predictive model scores

        Args:
            items: Items to rank

        Returns:
            Items with enhanced ranking scores
        """
        if not self.config.enabled:
            return items

        # Get predictions for all items
        for item in items:
            prediction = self.predictive_model.predict_importance(item)

            # Store prediction for later use
            item.prediction = prediction

            # Blend predictive score with rule-based score
            rule_based_score = getattr(
                self.feature_extractor.extract_all_features(item),
                'final_score',
                0.5
            )

            # Weighted blend: more predictive as model improves
            model_confidence = prediction.confidence
            blended_score = (
                model_confidence * prediction.predicted_score +
                (1 - model_confidence) * rule_based_score
            )

            # Update the ranking score
            if hasattr(item.ranking, 'final_score'):
                # Keep original but add predictive info
                item.ranking.predictive_score = prediction.predicted_score
                item.ranking.predictive_confidence = prediction.confidence
                item.ranking.blended_score = blended_score

        return items

    def select_learning_items(
        self, items: List[BriefItem], already_selected: List[BriefItem]
    ) -> List[LearningItem]:
        """
        Select items for active learning

        Args:
            items: All available items
            already_selected: Items already selected for display

        Returns:
            Items selected for learning (up to budget)
        """
        if not self.config.enabled:
            return []

        # Don't learn if not enough training data yet
        if len(self.predictive_model.training_data.labels) < self.config.min_samples_before_learning:
            return []

        # Get learning candidates from unselected items
        unselected_items = [item for item in items if item not in already_selected]
        candidates = self.active_learning.get_learning_candidates(
            unselected_items,
            max_candidates=self.config.learning_budget * 2  # Get more than needed
        )

        # Convert to LearningItems with priorities
        learning_items = []
        for item in candidates:
            priority = self._calculate_learning_priority(item)
            reason = self._get_learning_reason(item)

            learning_items.append(LearningItem(
                item=item,
                prediction=item.prediction,
                learning_priority=priority,
                reason=reason
            ))

        # Sort by priority and take top N
        learning_items.sort(key=lambda li: li.learning_priority, reverse=True)
        selected = learning_items[:self.config.learning_budget]

        # Track for this session
        self.current_session_learning_items = selected

        return selected

    def incorporate_session_feedback(self, feedback_events: List[Dict[str, Any]]):
        """
        Incorporate feedback from the current session

        Args:
            feedback_events: List of feedback events from this brief
        """
        if not self.config.enabled:
            return

        learning_feedback_count = 0

        for event in feedback_events:
            # Check if this was a learning item
            item_ref = event.get('item_id')
            if self._was_learning_item(item_ref):
                # Incorporate into model
                # Note: In real implementation, would need item data here
                # For now, just count
                learning_feedback_count += 1

        if learning_feedback_count > 0:
            print(f"Incorporated {learning_feedback_count} learning samples for user {self.user_id}")

    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status"""
        progress = self.active_learning.get_learning_progress()
        model_stats = self.predictive_model.get_stats()

        return {
            'enabled': self.config.enabled,
            'learning_budget': self.config.learning_budget,
            'uncertainty_threshold': self.config.uncertainty_threshold,
            'exploration_rate': self.config.exploration_rate,
            'current_session_learning_items': len(self.current_session_learning_items),
            'model_stats': model_stats,
            'learning_progress': progress,
            'learning_effective': (
                model_stats['training_samples'] >= self.config.min_samples_before_learning
            ),
        }

    def _calculate_learning_priority(self, item: BriefItem) -> float:
        """
        Calculate how valuable this item is for learning

        Higher priority = more uncertain + more diverse features
        """
        if not hasattr(item, 'prediction'):
            return 0.0

        prediction = item.prediction

        # Base priority = uncertainty (1 - confidence)
        base_priority = prediction.uncertainty

        # Boost for feature diversity (items with unusual combinations)
        diversity_boost = self._calculate_feature_diversity(item)

        # Boost for recency (recent feedback more valuable)
        recency_boost = self._calculate_recency_boost(item)

        # Combine factors
        priority = (
            0.6 * base_priority +
            0.3 * diversity_boost +
            0.1 * recency_boost
        )

        return min(1.0, priority)

    def _calculate_feature_diversity(self, item: BriefItem) -> float:
        """Calculate feature diversity (how unusual this item is)"""
        # Simplified: based on feature importance variance
        if not hasattr(item, 'prediction'):
            return 0.0

        importances = list(item.prediction.feature_importance.values())
        if not importances:
            return 0.0

        # Diversity = coefficient of variation (std/mean)
        mean_imp = sum(importances) / len(importances)
        if mean_imp == 0:
            return 0.0

        variance = sum((imp - mean_imp) ** 2 for imp in importances) / len(importances)
        std_dev = variance ** 0.5

        diversity = std_dev / mean_imp
        return min(1.0, diversity)  # Cap at 1.0

    def _calculate_recency_boost(self, item: BriefItem) -> float:
        """Boost for items that might provide recent feedback value"""
        # Simplified: slight boost for items within last hour
        hours_old = (datetime.now(timezone.utc) - item.timestamp_utc).total_seconds() / 3600
        return 0.2 if hours_old < 1 else 0.0

    def _get_learning_reason(self, item: BriefItem) -> str:
        """Get human-readable reason for selecting this item for learning"""
        if not hasattr(item, 'prediction'):
            return "Fallback selection"

        prediction = item.prediction

        if prediction.confidence < 0.3:
            return f"Very uncertain prediction ({prediction.confidence:.1f} confidence)"

        if prediction.uncertainty > 0.8:
            return f"High uncertainty ({prediction.uncertainty:.1f})"

        # Find most important feature
        if prediction.feature_importance:
            top_feature = max(prediction.feature_importance.items(), key=lambda x: x[1])
            return f"Learning about {top_feature[0]} ({top_feature[1]:.2f} importance)"

        return "Selected for model improvement"

    def _was_learning_item(self, item_ref: str) -> bool:
        """Check if item was selected for learning in current session"""
        return any(li.item.item_ref == item_ref for li in self.current_session_learning_items)

    def reset_session(self):
        """Reset learning tracking for new session"""
        self.current_session_learning_items = []


# Integration with ranking pipeline
class EnhancedRanker:
    """
    Enhanced ranker that integrates predictive models and active learning

    Usage:
        ranker = EnhancedRanker(user_id)
        ranked_items = ranker.rank_with_learning(items, available_slots=10)
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.active_learning = ActiveLearningIntegrator(user_id)

    def rank_with_learning(
        self,
        items: List[BriefItem],
        available_slots: int = 10,
        include_learning_items: bool = True
    ) -> Tuple[List[BriefItem], List[LearningItem]]:
        """
        Rank items with active learning integration

        Args:
            items: Items to rank
            available_slots: How many slots available for display
            include_learning_items: Whether to include learning items

        Returns:
            Tuple of (selected_items, learning_items)
        """
        # Step 1: Enhance ranking with predictions
        enhanced_items = self.active_learning.enhance_ranking_with_predictions(items)

        # Step 2: Sort by blended score (predictive + rule-based)
        enhanced_items.sort(
            key=lambda item: getattr(item.ranking, 'blended_score',
                                   getattr(item.ranking, 'final_score', 0.5)),
            reverse=True
        )

        # Step 3: Select top items for display
        selected_for_display = enhanced_items[:available_slots]

        # Step 4: Select additional learning items (if enabled)
        learning_items = []
        if include_learning_items:
            learning_items = self.active_learning.select_learning_items(
                enhanced_items, selected_for_display
            )

        return selected_for_display, learning_items

    def incorporate_feedback(self, feedback_events: List[Dict[str, Any]]):
        """Incorporate feedback from recent session"""
        self.active_learning.incorporate_session_feedback(feedback_events)

    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status"""
        return self.active_learning.get_learning_status()


# Global registry for easy access
_rankers_cache: Dict[str, EnhancedRanker] = {}


def get_enhanced_ranker(user_id: str) -> EnhancedRanker:
    """Get or create enhanced ranker for user"""
    if user_id not in _rankers_cache:
        _rankers_cache[user_id] = EnhancedRanker(user_id)
    return _rankers_cache[user_id]
