"""
Predictive Importance Model

Uses machine learning to predict item importance based on:
- Historical user feedback patterns
- Item features (content, source, timing, etc.)
- User preferences and behavior

Architecture:
- Feature extraction from items
- Training on historical feedback
- Prediction for new items
- Active learning for uncertainty
"""

import os
import pickle
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from packages.shared.schemas import BriefItem
from packages.database.models import FeedbackEvent
from packages.ranking.features import FeatureExtractor


@dataclass
class PredictionResult:
    """Result of importance prediction"""

    predicted_score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0 (higher = more confident)
    uncertainty: float  # 0.0-1.0 (higher = more uncertain)
    feature_importance: Dict[str, float]  # Which features influenced the prediction


@dataclass
class TrainingData:
    """Training data for the model"""

    features: np.ndarray
    labels: np.ndarray  # Actual importance scores (0.0-1.0)
    item_ids: List[str]
    timestamps: List[datetime]


class PredictiveImportanceModel:
    """
    Machine learning model for predicting item importance

    Features:
    - Content-based (topics, keywords, entities)
    - Source-based (credibility, engagement rate)
    - Temporal (time of day, day of week, urgency)
    - Social (VIP mentions, engagement patterns)
    - User preferences (learned weights)

    Training data from:
    - User feedback (clicks, saves, dismisses, thumb ratings)
    - Implicit signals (read time, scroll depth)
    - Explicit preferences (VIP lists, topic weights)
    """

    def __init__(
        self,
        user_id: str,
        model_path: Optional[str] = None,
        min_training_samples: int = 50,
        retrain_threshold: int = 100,  # Retrain every N new samples
    ):
        """
        Initialize predictive model

        Args:
            user_id: User ID for personalized model
            model_path: Optional path to save/load model
            min_training_samples: Minimum samples needed before training
            retrain_threshold: Retrain when this many new samples accumulate
        """
        self.user_id = user_id
        self.model_path = model_path or f"models/predictive_{user_id}.pkl"
        self.min_training_samples = min_training_samples
        self.retrain_threshold = retrain_threshold

        # ML components
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None

        # Training data tracking
        self.training_data = TrainingData(
            features=np.array([]),
            labels=np.array([]),
            item_ids=[],
            timestamps=[]
        )
        self.new_samples_since_train = 0

        # Feature extractor
        self.feature_extractor = FeatureExtractor()

        # Load existing model if available
        self._load_model()

    def predict_importance(self, item: BriefItem) -> PredictionResult:
        """
        Predict importance score for an item

        Args:
            item: Item to predict for

        Returns:
            PredictionResult with score, confidence, and uncertainty
        """
        if self.model is None or len(self.training_data.labels) < self.min_training_samples:
            # Not enough data - fall back to rule-based scoring
            return self._rule_based_prediction(item)

        # Extract features
        features = self._extract_features_for_prediction(item)
        if not features:
            return self._rule_based_prediction(item)

        # Scale features
        features_scaled = self.scaler.transform([features])

        # Get prediction and uncertainty
        predictions = []
        for estimator in self.model.estimators_:
            pred = estimator.predict(features_scaled)[0]
            predictions.append(pred)

        # Calculate statistics
        predicted_score = float(np.mean(predictions))
        std_dev = float(np.std(predictions))

        # Confidence = 1 / (1 + uncertainty)
        # Uncertainty based on prediction variance
        uncertainty = min(1.0, std_dev * 2)  # Scale variance to 0-1
        confidence = 1.0 - uncertainty

        # Feature importance from the model
        feature_names = [
            'relevance', 'urgency', 'credibility', 'impact', 'actionability',
            'topic_match', 'vip_mention', 'source_trust', 'temporal_urgency',
            'engagement_rate', 'content_length', 'entity_count'
        ]

        feature_importance = dict(zip(
            feature_names,
            self.model.feature_importances_
        ))

        return PredictionResult(
            predicted_score=max(0.0, min(1.0, predicted_score)),
            confidence=max(0.0, min(1.0, confidence)),
            uncertainty=uncertainty,
            feature_importance=feature_importance,
        )

    def add_feedback_sample(self, item: BriefItem, feedback: FeedbackEvent):
        """
        Add a feedback sample to training data

        Args:
            item: The item that received feedback
            feedback: The feedback event
        """
        # Extract features
        features = self._extract_features_for_training(item)
        if not features:
            return

        # Convert feedback to importance score (0.0-1.0)
        importance_score = self._feedback_to_importance_score(feedback)

        # Add to training data
        self.training_data.features = np.vstack([
            self.training_data.features,
            features
        ]) if self.training_data.features.size > 0 else np.array([features])

        self.training_data.labels = np.append(
            self.training_data.labels,
            importance_score
        )

        self.training_data.item_ids.append(item.item_ref)
        self.training_data.timestamps.append(feedback.created_at_utc)

        self.new_samples_since_train += 1

        # Retrain if enough new samples
        if self.new_samples_since_train >= self.retrain_threshold:
            self.train_model()
            self.new_samples_since_train = 0

    def train_model(self, force: bool = False) -> bool:
        """
        Train the predictive model

        Args:
            force: Force training even if not enough samples

        Returns:
            True if model was trained, False otherwise
        """
        if len(self.training_data.labels) < self.min_training_samples and not force:
            return False

        # Prepare data
        X = self.training_data.features
        y = self.training_data.labels

        # Split for validation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"Model trained for user {self.user_id}:")
        print(".4f")
        print(".4f")

        # Save model
        self._save_model()

        return True

    def get_uncertain_predictions(self, items: List[BriefItem], threshold: float = 0.7) -> List[BriefItem]:
        """
        Get items with uncertain predictions (for active learning)

        Args:
            items: Items to check
            threshold: Confidence threshold (lower = more uncertain)

        Returns:
            Items with low confidence predictions
        """
        uncertain_items = []

        for item in items:
            prediction = self.predict_importance(item)
            if prediction.confidence < threshold:
                # Add prediction info to item for later use
                item.prediction = prediction
                uncertain_items.append(item)

        return uncertain_items

    def _extract_features_for_prediction(self, item: BriefItem) -> Optional[List[float]]:
        """Extract features for prediction (same as training but no feedback)"""
        try:
            # Get standard ranking features
            ranking_features = self.feature_extractor.extract_all_features(item)

            # Add prediction-specific features
            features = [
                ranking_features.relevance,
                ranking_features.urgency,
                ranking_features.credibility,
                ranking_features.impact,
                ranking_features.actionability,

                # Additional features for ML
                self._calculate_topic_match(item),
                self._check_vip_mention(item),
                self._get_source_trust(item),
                self._calculate_temporal_urgency(item),
                self._get_engagement_rate(item),
                self._get_content_length(item),
                self._get_entity_count(item),
            ]

            return features

        except Exception:
            return None

    def _extract_features_for_training(self, item: BriefItem) -> Optional[List[float]]:
        """Extract features for training (includes historical patterns)"""
        # Same as prediction features for now
        return self._extract_features_for_prediction(item)

    def _feedback_to_importance_score(self, feedback: FeedbackEvent) -> float:
        """
        Convert feedback event to importance score

        Scale: 0.0 (dismissed) → 1.0 (saved + thumb up)
        """
        base_scores = {
            'open': 0.6,          # Just opened/clicked
            'save': 0.9,          # Explicitly saved
            'dismiss': 0.1,       # Dismissed
            'thumb_up': 0.8,      # Positive feedback
            'thumb_down': 0.2,    # Negative feedback
            'less_like_this': 0.1, # Don't want this type
        }

        base_score = base_scores.get(feedback.event_type, 0.5)

        # Boost for multiple interactions
        if hasattr(feedback, 'interaction_count'):
            base_score = min(1.0, base_score + (feedback.interaction_count - 1) * 0.1)

        return base_score

    def _rule_based_prediction(self, item: BriefItem) -> PredictionResult:
        """Fallback rule-based prediction when no ML model available"""
        try:
            features = self.feature_extractor.extract_all_features(item)
            score = features.final_score if hasattr(features, 'final_score') else 0.5

            return PredictionResult(
                predicted_score=score,
                confidence=0.3,  # Low confidence (rule-based)
                uncertainty=0.7,
                feature_importance={
                    'rule_based': 1.0,
                    'relevance': getattr(features, 'relevance', 0.0),
                    'urgency': getattr(features, 'urgency', 0.0),
                }
            )
        except Exception:
            return PredictionResult(
                predicted_score=0.5,
                confidence=0.1,
                uncertainty=0.9,
                feature_importance={'fallback': 1.0}
            )

    def _calculate_topic_match(self, item: BriefItem) -> float:
        """Calculate how well item matches user's preferred topics"""
        # Simplified: would use learned topic weights
        return 0.5  # Placeholder

    def _check_vip_mention(self, item: BriefItem) -> float:
        """Check if item mentions VIP people"""
        # Simplified: would check entity list against VIPs
        return 0.0 if not item.entities else 0.3

    def _get_source_trust(self, item: BriefItem) -> float:
        """Get learned trust score for source"""
        return self.feature_extractor.extract_credibility(item)

    def _calculate_temporal_urgency(self, item: BriefItem) -> float:
        """Calculate urgency based on timing"""
        # Simplified: higher for recent items
        hours_old = (datetime.now(timezone.utc) - item.timestamp_utc).total_seconds() / 3600
        return max(0.0, 1.0 - (hours_old / 24))  # Decay over 24 hours

    def _get_engagement_rate(self, item: BriefItem) -> float:
        """Get historical engagement rate for similar items"""
        # Simplified: would query feedback history
        return 0.4  # Placeholder

    def _get_content_length(self, item: BriefItem) -> float:
        """Get normalized content length"""
        total_length = len(item.title) + len(item.summary) + len(item.why_it_matters)
        # Normalize to 0-1 scale (assuming 1000 chars = max)
        return min(1.0, total_length / 1000)

    def _get_entity_count(self, item: BriefItem) -> float:
        """Get normalized entity count"""
        entity_count = len(item.entities) if item.entities else 0
        # Normalize to 0-1 scale (assuming 10 entities = max)
        return min(1.0, entity_count / 10)

    def _save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'training_data': self.training_data,
                    'user_id': self.user_id,
                }, f)
        except Exception as e:
            print(f"Failed to save model: {e}")

    def _load_model(self):
        """Load model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.training_data = data['training_data']
        except Exception as e:
            print(f"Failed to load model: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            'user_id': self.user_id,
            'has_model': self.model is not None,
            'training_samples': len(self.training_data.labels),
            'min_samples_required': self.min_training_samples,
            'new_samples_pending': self.new_samples_since_train,
            'model_path': self.model_path,
        }


class ActiveLearningManager:
    """
    Manages active learning from uncertain predictions

    Strategy:
    1. Identify items with uncertain predictions
    2. Show them to user and collect feedback
    3. Use feedback to improve model
    4. Repeat to reduce uncertainty over time
    """

    def __init__(self, user_id: str, uncertainty_threshold: float = 0.6):
        """
        Initialize active learning manager

        Args:
            user_id: User ID
            uncertainty_threshold: Threshold below which items are "uncertain"
        """
        self.user_id = user_id
        self.uncertainty_threshold = uncertainty_threshold
        self.predictive_model = PredictiveImportanceModel(user_id)

    def get_learning_candidates(self, items: List[BriefItem], max_candidates: int = 5) -> List[BriefItem]:
        """
        Get items that would benefit most from user feedback

        Args:
            items: Candidate items
            max_candidates: Maximum number to return

        Returns:
            Items with uncertain predictions (sorted by uncertainty)
        """
        uncertain_items = self.predictive_model.get_uncertain_predictions(
            items, threshold=self.uncertainty_threshold
        )

        # Sort by uncertainty (highest first)
        uncertain_items.sort(
            key=lambda item: getattr(item, 'prediction', PredictionResult(0, 0, 1, {})).uncertainty,
            reverse=True
        )

        return uncertain_items[:max_candidates]

    def incorporate_feedback(self, item: BriefItem, feedback: FeedbackEvent):
        """
        Incorporate user feedback to improve the model

        Args:
            item: Item that received feedback
            feedback: The feedback event
        """
        self.predictive_model.add_feedback_sample(item, feedback)

        # Retrain if enough new samples
        self.predictive_model.train_model()

    def should_show_for_learning(self, item: BriefItem) -> bool:
        """
        Decide if item should be shown primarily for learning

        Returns True if:
        - Prediction is very uncertain
        - Item would help diversify training data
        - Model needs more samples in this feature space
        """
        prediction = self.predictive_model.predict_importance(item)

        # Very uncertain predictions are great for learning
        if prediction.confidence < 0.4:
            return True

        # Items that would fill gaps in training data
        training_count = len(self.predictive_model.training_data.labels)
        if training_count < 100:
            # Early stages: show more for learning
            return prediction.confidence < 0.7

        return False

    def get_learning_progress(self) -> Dict[str, Any]:
        """Get active learning progress statistics"""
        model_stats = self.predictive_model.get_stats()

        return {
            'model_stats': model_stats,
            'uncertainty_threshold': self.uncertainty_threshold,
            'learning_effective': model_stats['training_samples'] >= 50,
            'average_confidence': None,  # Would need to calculate from recent predictions
        }


# Singleton pattern for easy access
_models_cache: Dict[str, PredictiveImportanceModel] = {}
_managers_cache: Dict[str, ActiveLearningManager] = {}


def get_predictive_model(user_id: str) -> PredictiveImportanceModel:
    """Get or create predictive model for user"""
    if user_id not in _models_cache:
        _models_cache[user_id] = PredictiveImportanceModel(user_id)
    return _models_cache[user_id]


def get_active_learning_manager(user_id: str) -> ActiveLearningManager:
    """Get or create active learning manager for user"""
    if user_id not in _managers_cache:
        _managers_cache[user_id] = ActiveLearningManager(user_id)
    return _managers_cache[user_id]
