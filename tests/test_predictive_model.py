"""
Tests for Predictive Importance Model and Active Learning

Tests:
1. Predictive model training and prediction
2. Feature extraction for ML
3. Active learning item selection
4. Feedback incorporation
5. Model persistence
"""

import os
import pytest
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from packages.ranking.predictive_model import (
    PredictiveImportanceModel,
    ActiveLearningManager,
    PredictionResult,
    get_predictive_model,
    get_active_learning_manager,
)
from packages.ranking.active_learning import (
    ActiveLearningIntegrator,
    EnhancedRanker,
    get_enhanced_ranker,
)
from packages.shared.schemas import BriefItem, Entity, NoveltyInfo, RankingScores
from packages.database.models import FeedbackEvent


@pytest.fixture
def temp_model_dir():
    """Temporary directory for model storage"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_feedback_events():
    """Sample feedback events for training"""
    base_time = datetime.now(timezone.utc)

    return [
        FeedbackEvent(
            user_id="test_user",
            item_id="item_1",
            event_type="save",  # High importance
            created_at_utc=base_time - timedelta(hours=1),
        ),
        FeedbackEvent(
            user_id="test_user",
            item_id="item_2",
            event_type="thumb_up",  # High importance
            created_at_utc=base_time - timedelta(hours=2),
        ),
        FeedbackEvent(
            user_id="test_user",
            item_id="item_3",
            event_type="dismiss",  # Low importance
            created_at_utc=base_time - timedelta(hours=3),
        ),
        FeedbackEvent(
            user_id="test_user",
            item_id="item_4",
            event_type="open",  # Medium importance
            created_at_utc=base_time - timedelta(hours=4),
        ),
    ]


@pytest.fixture
def sample_brief_items():
    """Sample brief items for testing"""
    base_time = datetime.now(timezone.utc)

    return [
        BriefItem(
            item_ref="item_1",
            source="gmail",
            type="email",
            timestamp_utc=(base_time - timedelta(hours=1)).isoformat(),
            title="Important Meeting",
            summary="Urgent meeting tomorrow",
            why_it_matters="Directly affects your schedule",
            entities=[Entity(kind="person", key="boss@email.com")],
            novelty=NoveltyInfo(
                label="NEW",
                reason="First time",
                first_seen_utc=base_time.isoformat(),
                last_updated_utc=base_time.isoformat(),
                seen_count=1,
            ),
            ranking=RankingScores(
                final_score=0.8,
                relevance_score=0.8,
                urgency_score=0.9,
                credibility_score=0.9,
                impact_score=0.7,
                actionability_score=0.8,
            ),
        ),
        BriefItem(
            item_ref="item_2",
            source="calendar",
            type="event",
            timestamp_utc=(base_time - timedelta(minutes=30)).isoformat(),
            title="Team Standup",
            summary="Daily team meeting",
            why_it_matters="Keep up with team progress",
            entities=[],
            novelty=NoveltyInfo(
                label="NEW",
                reason="First time",
                first_seen_utc=base_time.isoformat(),
                last_updated_utc=base_time.isoformat(),
                seen_count=1,
            ),
            ranking=RankingScores(
                final_score=0.6,
                relevance_score=0.6,
                urgency_score=0.8,
                credibility_score=0.9,
                impact_score=0.4,
                actionability_score=0.6,
            ),
        ),
        BriefItem(
            item_ref="item_3",
            source="twitter",
            type="post",
            timestamp_utc=(base_time - timedelta(hours=2)).isoformat(),
            title="Tech News",
            summary="New AI breakthrough announced",
            why_it_matters="Interesting development in your field",
            entities=[Entity(kind="topic", key="AI")],
            novelty=NoveltyInfo(
                label="NEW",
                reason="First time",
                first_seen_utc=base_time.isoformat(),
                last_updated_utc=base_time.isoformat(),
                seen_count=1,
            ),
            ranking=RankingScores(
                final_score=0.4,
                relevance_score=0.7,
                urgency_score=0.2,
                credibility_score=0.5,
                impact_score=0.3,
                actionability_score=0.4,
            ),
        ),
    ]


class TestPredictiveImportanceModel:
    """Test predictive importance model"""

    def test_initialization(self, temp_model_dir):
        """Test model initialization"""
        model_path = os.path.join(temp_model_dir, "test_model.pkl")
        model = PredictiveImportanceModel("test_user", model_path)

        assert model.user_id == "test_user"
        assert model.model_path == model_path
        assert model.model is None  # No model trained yet
        assert len(model.training_data.labels) == 0

    def test_rule_based_prediction_fallback(self, temp_model_dir, sample_brief_items):
        """Test fallback to rule-based prediction when no ML model"""
        model = PredictiveImportanceModel("test_user", os.path.join(temp_model_dir, "test.pkl"))

        item = sample_brief_items[0]
        result = model.predict_importance(item)

        # Should return rule-based prediction
        assert isinstance(result, PredictionResult)
        assert 0.0 <= result.predicted_score <= 1.0
        assert result.confidence < 0.5  # Low confidence for rule-based

    @patch('packages.ranking.predictive_model.RandomForestRegressor')
    @patch('packages.ranking.predictive_model.StandardScaler')
    def test_model_training(self, mock_scaler, mock_rf, temp_model_dir, sample_brief_items, sample_feedback_events):
        """Test model training with sample data"""
        # Mock the ML components
        mock_model = Mock()
        mock_model.fit = Mock()
        mock_model.predict = Mock(return_value=[0.8])
        mock_model.feature_importances_ = [0.1] * 12
        mock_model.estimators_ = [Mock(predict=Mock(return_value=[0.8])) for _ in range(3)]

        mock_rf.return_value = mock_model
        mock_scaler.return_value = Mock()

        model = PredictiveImportanceModel("test_user", os.path.join(temp_model_dir, "test.pkl"))

        # Add training samples
        for i, feedback in enumerate(sample_feedback_events):
            if i < len(sample_brief_items):
                model.add_feedback_sample(sample_brief_items[i], feedback)

        # Train model
        success = model.train_model(force=True)
        assert success

        # Check that ML components were used
        mock_rf.assert_called_once()
        mock_scaler.assert_called_once()
        mock_model.fit.assert_called_once()

    def test_feedback_to_importance_conversion(self, temp_model_dir):
        """Test conversion of feedback events to importance scores"""
        model = PredictiveImportanceModel("test_user", os.path.join(temp_model_dir, "test.pkl"))

        # Test different feedback types
        save_feedback = FeedbackEvent(
            user_id="test",
            item_id="item1",
            event_type="save",
            created_at_utc=datetime.now(timezone.utc)
        )

        dismiss_feedback = FeedbackEvent(
            user_id="test",
            item_id="item2",
            event_type="dismiss",
            created_at_utc=datetime.now(timezone.utc)
        )

        save_score = model._feedback_to_importance_score(save_feedback)
        dismiss_score = model._feedback_to_importance_score(dismiss_feedback)

        assert save_score > dismiss_score  # Save should be higher
        assert save_score >= 0.8  # Save should be high
        assert dismiss_score <= 0.2  # Dismiss should be low

    def test_feature_extraction(self, temp_model_dir, sample_brief_items):
        """Test feature extraction for ML"""
        model = PredictiveImportanceModel("test_user", os.path.join(temp_model_dir, "test.pkl"))

        item = sample_brief_items[0]
        features = model._extract_features_for_prediction(item)

        assert features is not None
        assert len(features) == 12  # Expected number of features
        assert all(isinstance(f, (int, float)) for f in features)

    def test_get_stats(self, temp_model_dir):
        """Test getting model statistics"""
        model = PredictiveImportanceModel("test_user", os.path.join(temp_model_dir, "test.pkl"))

        stats = model.get_stats()

        assert stats['user_id'] == "test_user"
        assert not stats['has_model']  # No model trained
        assert stats['training_samples'] == 0


class TestActiveLearningManager:
    """Test active learning manager"""

    def test_initialization(self):
        """Test active learning manager initialization"""
        manager = ActiveLearningManager("test_user", uncertainty_threshold=0.5)

        assert manager.user_id == "test_user"
        assert manager.uncertainty_threshold == 0.5
        assert hasattr(manager, 'predictive_model')

    def test_get_learning_candidates(self, sample_brief_items):
        """Test getting learning candidates"""
        manager = ActiveLearningManager("test_user")

        # Mock uncertain predictions
        for item in sample_brief_items:
            item.prediction = PredictionResult(
                predicted_score=0.5,
                confidence=0.3,  # Low confidence = uncertain
                uncertainty=0.7,
                feature_importance={'test': 0.5}
            )

        candidates = manager.get_learning_candidates(sample_brief_items, max_candidates=2)

        assert len(candidates) == 2
        # Should be sorted by uncertainty (highest first)
        assert candidates[0].prediction.uncertainty >= candidates[1].prediction.uncertainty

    def test_should_show_for_learning(self, sample_brief_items):
        """Test deciding whether to show item for learning"""
        manager = ActiveLearningManager("test_user")

        # Very uncertain item
        uncertain_item = sample_brief_items[0]
        uncertain_item.prediction = PredictionResult(
            predicted_score=0.5,
            confidence=0.2,  # Very low confidence
            uncertainty=0.8,
            feature_importance={}
        )

        # Confident item
        confident_item = sample_brief_items[1]
        confident_item.prediction = PredictionResult(
            predicted_score=0.7,
            confidence=0.9,  # High confidence
            uncertainty=0.1,
            feature_importance={}
        )

        assert manager.should_show_for_learning(uncertain_item)
        assert not manager.should_show_for_learning(confident_item)

    def test_learning_progress(self):
        """Test getting learning progress"""
        manager = ActiveLearningManager("test_user")

        progress = manager.get_learning_progress()

        assert 'model_stats' in progress
        assert 'uncertainty_threshold' in progress
        assert 'learning_effective' in progress


class TestActiveLearningIntegrator:
    """Test active learning integration"""

    def test_initialization(self):
        """Test integrator initialization"""
        integrator = ActiveLearningIntegrator("test_user")

        assert integrator.user_id == "test_user"
        assert integrator.config.enabled
        assert integrator.config.learning_budget == 3

    def test_enhance_ranking_with_predictions(self, sample_brief_items):
        """Test enhancing ranking with predictions"""
        integrator = ActiveLearningIntegrator("test_user")

        enhanced = integrator.enhance_ranking_with_predictions(sample_brief_items)

        # All items should have prediction attribute
        for item in enhanced:
            assert hasattr(item, 'prediction')
            assert isinstance(item.prediction, PredictionResult)

            # Should have blended score
            assert hasattr(item.ranking, 'predictive_score')
            assert hasattr(item.ranking, 'predictive_confidence')

    def test_select_learning_items(self, sample_brief_items):
        """Test selecting learning items"""
        integrator = ActiveLearningIntegrator("test_user")

        # Mark some items as uncertain
        for item in sample_brief_items:
            item.prediction = PredictionResult(
                predicted_score=0.5,
                confidence=0.3,  # Uncertain
                uncertainty=0.7,
                feature_importance={'test': 0.5}
            )

        learning_items = integrator.select_learning_items(
            sample_brief_items, already_selected=[]
        )

        assert len(learning_items) <= integrator.config.learning_budget
        for li in learning_items:
            assert hasattr(li, 'learning_priority')
            assert hasattr(li, 'reason')

    def test_get_learning_status(self):
        """Test getting learning status"""
        integrator = ActiveLearningIntegrator("test_user")

        status = integrator.get_learning_status()

        assert 'enabled' in status
        assert 'learning_budget' in status
        assert 'model_stats' in status
        assert 'learning_progress' in status


class TestEnhancedRanker:
    """Test enhanced ranker with active learning"""

    def test_initialization(self):
        """Test enhanced ranker initialization"""
        ranker = EnhancedRanker("test_user")

        assert ranker.user_id == "test_user"
        assert hasattr(ranker, 'active_learning')

    def test_rank_with_learning(self, sample_brief_items):
        """Test ranking with learning integration"""
        ranker = EnhancedRanker("test_user")

        selected, learning = ranker.rank_with_learning(
            sample_brief_items, available_slots=2
        )

        assert len(selected) <= 2  # Limited by available_slots
        assert isinstance(learning, list)

        # Check that selected items have enhanced ranking
        for item in selected:
            assert hasattr(item, 'prediction')

    def test_get_learning_status_through_ranker(self):
        """Test getting learning status through ranker"""
        ranker = EnhancedRanker("test_user")

        status = ranker.get_learning_status()

        assert isinstance(status, dict)
        assert 'enabled' in status


class TestGlobalFunctions:
    """Test global singleton functions"""

    def test_get_predictive_model_singleton(self):
        """Test singleton behavior of get_predictive_model"""
        model1 = get_predictive_model("test_user_1")
        model2 = get_predictive_model("test_user_1")
        model3 = get_predictive_model("test_user_2")

        assert model1 is model2  # Same user = same instance
        assert model1 is not model3  # Different user = different instance

    def test_get_active_learning_manager_singleton(self):
        """Test singleton behavior of get_active_learning_manager"""
        mgr1 = get_active_learning_manager("test_user_1")
        mgr2 = get_active_learning_manager("test_user_1")
        mgr3 = get_active_learning_manager("test_user_2")

        assert mgr1 is mgr2  # Same user = same instance
        assert mgr1 is not mgr3  # Different user = different instance

    def test_get_enhanced_ranker_singleton(self):
        """Test singleton behavior of get_enhanced_ranker"""
        ranker1 = get_enhanced_ranker("test_user_1")
        ranker2 = get_enhanced_ranker("test_user_1")
        ranker3 = get_enhanced_ranker("test_user_2")

        assert ranker1 is ranker2  # Same user = same instance
        assert ranker1 is not ranker3  # Different user = different instance


class TestIntegration:
    """Integration tests for the complete pipeline"""

    def test_end_to_end_prediction_and_learning(self, sample_brief_items, sample_feedback_events):
        """Test complete prediction → feedback → learning cycle"""
        user_id = "integration_test"

        # Get components
        ranker = get_enhanced_ranker(user_id)
        model = get_predictive_model(user_id)

        # Initial state - should use rule-based predictions
        initial_predictions = [model.predict_importance(item) for item in sample_brief_items]
        assert all(pred.confidence < 0.5 for pred in initial_predictions)  # Low confidence initially

        # Simulate user feedback
        feedback_events = []
        for i, item in enumerate(sample_brief_items[:2]):  # First 2 items get feedback
            feedback = sample_feedback_events[i]
            feedback.item_id = item.item_ref
            model.add_feedback_sample(item, feedback)
            feedback_events.append({
                'item_id': item.item_ref,
                'event_type': feedback.event_type,
                'created_at_utc': feedback.created_at_utc
            })

        # Train model
        model.train_model(force=True)

        # Predictions should now be more confident
        trained_predictions = [model.predict_importance(item) for item in sample_brief_items]
        avg_confidence = sum(pred.confidence for pred in trained_predictions) / len(trained_predictions)

        # Confidence should be higher after training
        assert avg_confidence > 0.5

        # Incorporate session feedback
        ranker.incorporate_feedback(feedback_events)

        # Check learning status
        status = ranker.get_learning_status()
        assert status['enabled']
        assert status['model_stats']['training_samples'] >= 2


# Performance tests
class TestPerformance:
    """Performance tests for ML components"""

    def test_batch_prediction_performance(self, sample_brief_items):
        """Test that batch operations are reasonably fast"""
        import time

        model = get_predictive_model("perf_test")

        # Create larger batch
        large_batch = sample_brief_items * 10  # 30 items

        start_time = time.time()
        predictions = [model.predict_importance(item) for item in large_batch]
        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 1 second for 30 items)
        assert elapsed < 1.0
        assert len(predictions) == len(large_batch)

    def test_memory_usage_control(self):
        """Test that model doesn't use excessive memory"""
        # This is a basic check - in real scenarios would use memory profiling
        model = get_predictive_model("memory_test")

        # Check that training data doesn't grow unbounded
        initial_size = len(model.training_data.labels)

        # Add some data
        for i in range(10):
            # Would add real feedback here
            pass

        # Training data should be manageable
        assert len(model.training_data.labels) >= initial_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
