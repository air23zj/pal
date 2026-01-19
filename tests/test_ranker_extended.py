"""
Extended tests for ranker.py to increase coverage to 80%+
"""
import pytest
from datetime import datetime, timezone, timedelta
from packages.ranking.ranker import (
    Ranker, RankingWeights, SelectionCaps, rank_items, select_top_highlights
)
from packages.shared.schemas import BriefItem, NoveltyInfo, RankingScores, Entity


def create_test_item(
    item_id: str,
    relevance: float = 0.5,
    urgency: float = 0.5,
    final_score: float = 0.5,
) -> BriefItem:
    """Helper to create test items"""
    return BriefItem(
        item_ref=item_id,
        source='gmail',
        type='email',
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        title=f'Test {item_id}',
        summary='Test summary',
        why_it_matters='Test',
        entities=[],
        novelty=NoveltyInfo(
            label='NEW',
            reason='Test',
            first_seen_utc=datetime.now(timezone.utc).isoformat()
        ),
        ranking=RankingScores(
            relevance_score=relevance,
            urgency_score=urgency,
            credibility_score=0.5,
            actionability_score=0.5,
            impact_score=0.5,  # Added missing field
            final_score=final_score
        ),
        evidence=[],
        suggested_actions=[]
    )


class TestRankingWeights:
    """Test RankingWeights class"""
    
    def test_weights_normalize(self):
        """Test weight normalization"""
        weights = RankingWeights(
            relevance=0.5,
            urgency=0.3,
            credibility=0.1,
            impact=0.05,
            actionability=0.05
        )
        
        normalized = weights.normalize()
        
        # Sum should be 1.0
        total = (normalized.relevance + normalized.urgency + 
                normalized.credibility + normalized.impact + 
                normalized.actionability)
        assert abs(total - 1.0) < 0.001
    
    def test_weights_normalize_already_normalized(self):
        """Test normalizing already normalized weights"""
        weights = RankingWeights()  # Default weights should sum to 1.0
        normalized = weights.normalize()
        
        # Should be very close to original
        assert abs(normalized.relevance - weights.relevance) < 0.01
    
    def test_weights_normalize_uneven(self):
        """Test normalizing uneven weights"""
        weights = RankingWeights(
            relevance=1.0,
            urgency=2.0,
            credibility=3.0,
            impact=4.0,
            actionability=5.0
        )
        
        normalized = weights.normalize()
        
        # Should preserve ratios
        assert normalized.actionability > normalized.relevance
        # Sum should be 1.0
        total = (normalized.relevance + normalized.urgency + 
                normalized.credibility + normalized.impact + 
                normalized.actionability)
        assert abs(total - 1.0) < 0.001
    
    def test_weights_normalize_preserves_ratios(self):
        """Test that normalization preserves weight ratios"""
        weights = RankingWeights(
            relevance=2.0,
            urgency=1.0,
            credibility=1.0,
            impact=1.0,
            actionability=1.0
        )
        
        normalized = weights.normalize()
        
        # Relevance should still be largest
        assert normalized.relevance > normalized.urgency
        assert normalized.relevance > normalized.credibility


class TestSelectionCaps:
    """Test SelectionCaps dataclass"""
    
    def test_caps_defaults(self):
        """Test default selection caps"""
        caps = SelectionCaps()
        
        assert caps.max_highlights == 5
        assert caps.max_items_per_module == 8
        assert caps.default_items_per_module == 3
        assert caps.max_total_items == 30
    
    def test_caps_custom(self):
        """Test custom selection caps"""
        caps = SelectionCaps(
            max_highlights=10,
            max_items_per_module=15,
            default_items_per_module=5,
            max_total_items=50
        )
        
        assert caps.max_highlights == 10
        assert caps.max_items_per_module == 15
        assert caps.default_items_per_module == 5
        assert caps.max_total_items == 50


class TestRankerSelectItemsPerModule:
    """Test select_items_per_module method"""
    
    def test_select_items_per_module_with_ranking(self):
        """Test selecting items when already ranked"""
        ranker = Ranker()
        
        items = [
            create_test_item('item1', final_score=0.9),
            create_test_item('item2', final_score=0.8),
            create_test_item('item3', final_score=0.7),
            create_test_item('item4', final_score=0.6),
        ]
        
        selected = ranker.select_items_per_module(items, 'email', max_count=2)
        
        assert len(selected) == 2
        assert selected[0].item_ref == 'item1'
        assert selected[1].item_ref == 'item2'
    
    def test_select_items_per_module_without_ranking(self):
        """Test selecting items when not yet ranked"""
        ranker = Ranker()
        
        # Create items without ranking
        items = [
            create_test_item('item1', final_score=0.5),
            create_test_item('item2', final_score=0.5),
        ]
        # Clear rankings to simulate unranked items
        for item in items:
            item.ranking = None
        
        selected = ranker.select_items_per_module(items, 'email', max_count=1)
        
        # Should rank and select
        assert len(selected) <= 1
    
    def test_select_items_per_module_default_cap(self):
        """Test using default cap from SelectionCaps"""
        caps = SelectionCaps(max_items_per_module=3)
        ranker = Ranker(caps=caps)
        
        items = [
            create_test_item(f'item{i}', final_score=1.0-i*0.1)
            for i in range(10)
        ]
        
        selected = ranker.select_items_per_module(items, 'email')
        
        # Should use default cap of 3
        assert len(selected) == 3
    
    def test_select_items_per_module_fewer_items_than_cap(self):
        """Test when fewer items than cap"""
        ranker = Ranker()
        
        items = [
            create_test_item('item1', final_score=0.8),
            create_test_item('item2', final_score=0.7),
        ]
        
        selected = ranker.select_items_per_module(items, 'email', max_count=5)
        
        # Should return all items
        assert len(selected) == 2


class TestRankerEnforceTotalCap:
    """Test enforce_total_cap method"""
    
    def test_enforce_total_cap_with_ranking(self):
        """Test enforcing total cap on ranked items"""
        ranker = Ranker()
        
        items = [
            create_test_item(f'item{i}', final_score=1.0-i*0.05)
            for i in range(20)
        ]
        
        capped = ranker.enforce_total_cap(items, max_total=10)
        
        assert len(capped) == 10
        # Should be highest scored items
        assert capped[0].item_ref == 'item0'
    
    def test_enforce_total_cap_without_ranking(self):
        """Test enforcing cap on unranked items"""
        ranker = Ranker()
        
        items = [
            create_test_item(f'item{i}', final_score=0.5)
            for i in range(15)
        ]
        # Clear rankings
        for item in items:
            item.ranking = None
        
        capped = ranker.enforce_total_cap(items, max_total=5)
        
        # Should rank first, then cap
        assert len(capped) == 5
    
    def test_enforce_total_cap_default(self):
        """Test using default total cap"""
        caps = SelectionCaps(max_total_items=20)
        ranker = Ranker(caps=caps)
        
        items = [
            create_test_item(f'item{i}', final_score=0.8)
            for i in range(30)
        ]
        
        capped = ranker.enforce_total_cap(items)
        
        # Should use default cap of 20
        assert len(capped) == 20
    
    def test_enforce_total_cap_fewer_items(self):
        """Test when fewer items than cap"""
        ranker = Ranker()
        
        items = [
            create_test_item(f'item{i}', final_score=0.8)
            for i in range(5)
        ]
        
        capped = ranker.enforce_total_cap(items, max_total=30)
        
        # Should return all items
        assert len(capped) == 5
    
    def test_enforce_total_cap_resorts(self):
        """Test that enforce_total_cap resorts items"""
        ranker = Ranker()
        
        items = [
            create_test_item('item1', final_score=0.6),
            create_test_item('item2', final_score=0.9),
            create_test_item('item3', final_score=0.7),
        ]
        
        capped = ranker.enforce_total_cap(items, max_total=2)
        
        # Should be sorted by score
        assert capped[0].item_ref == 'item2'
        assert capped[1].item_ref == 'item3'


class TestRankerAdjustWeightsFromFeedback:
    """Test adjust_weights_from_feedback method"""
    
    def test_adjust_weights_positive_feedback(self):
        """Test weight adjustment with positive feedback"""
        ranker = Ranker()
        
        feedback = [
            {'event_type': 'thumb_up', 'item_id': 'item1'},
            {'event_type': 'thumb_up', 'item_id': 'item2'},
            {'event_type': 'thumb_up', 'item_id': 'item3'},
            {'event_type': 'thumb_down', 'item_id': 'item4'},
        ]
        
        adjusted = ranker.adjust_weights_from_feedback(feedback)
        
        # With positive > negative * 2, should return current weights
        assert adjusted == ranker.weights
    
    def test_adjust_weights_negative_feedback(self):
        """Test weight adjustment with negative feedback"""
        ranker = Ranker()
        original_relevance = ranker.weights.relevance
        original_urgency = ranker.weights.urgency
        
        feedback = [
            {'event_type': 'thumb_down', 'item_id': 'item1'},
            {'event_type': 'thumb_down', 'item_id': 'item2'},
            {'event_type': 'thumb_down', 'item_id': 'item3'},
            {'event_type': 'thumb_up', 'item_id': 'item4'},
        ]
        
        adjusted = ranker.adjust_weights_from_feedback(feedback)
        
        # With negative > positive, should adjust weights
        # Relevance should increase, urgency should decrease
        assert adjusted.relevance >= original_relevance
    
    def test_adjust_weights_no_feedback(self):
        """Test weight adjustment with no feedback"""
        ranker = Ranker()
        
        feedback = []
        
        adjusted = ranker.adjust_weights_from_feedback(feedback)
        
        # Should return current weights
        assert adjusted == ranker.weights
    
    def test_adjust_weights_mixed_feedback(self):
        """Test weight adjustment with mixed feedback"""
        ranker = Ranker()
        
        feedback = [
            {'event_type': 'thumb_up', 'item_id': 'item1'},
            {'event_type': 'thumb_down', 'item_id': 'item2'},
        ]
        
        adjusted = ranker.adjust_weights_from_feedback(feedback)
        
        # Should return some adjusted weights
        assert isinstance(adjusted, RankingWeights)
    
    def test_adjust_weights_normalizes_result(self):
        """Test that adjusted weights are normalized"""
        ranker = Ranker()
        
        feedback = [
            {'event_type': 'thumb_down', 'item_id': f'item{i}'}
            for i in range(5)
        ]
        
        adjusted = ranker.adjust_weights_from_feedback(feedback)
        
        # Weights should sum to ~1.0
        total = (adjusted.relevance + adjusted.urgency + 
                adjusted.credibility + adjusted.impact + 
                adjusted.actionability)
        assert abs(total - 1.0) < 0.001


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_rank_items_function(self):
        """Test rank_items convenience function"""
        items = [
            create_test_item('item1', final_score=0.3),
            create_test_item('item2', final_score=0.9),
            create_test_item('item3', final_score=0.6),
        ]
        # Clear rankings
        for item in items:
            item.ranking = None
        
        ranked = rank_items(items)
        
        assert len(ranked) == 3
        # Should be sorted by score
        assert ranked[0].ranking.final_score >= ranked[1].ranking.final_score
    
    def test_rank_items_with_preferences(self):
        """Test rank_items with user preferences"""
        items = [
            create_test_item('item1'),
            create_test_item('item2'),
        ]
        for item in items:
            item.ranking = None
        
        prefs = {'topics': ['test']}
        ranked = rank_items(items, user_preferences=prefs)
        
        assert len(ranked) == 2
    
    def test_rank_items_with_custom_weights(self):
        """Test rank_items with custom weights"""
        items = [
            create_test_item('item1'),
            create_test_item('item2'),
        ]
        for item in items:
            item.ranking = None
        
        weights = RankingWeights(relevance=0.8, urgency=0.2)
        ranked = rank_items(items, weights=weights)
        
        assert len(ranked) == 2
    
    def test_select_top_highlights_function(self):
        """Test select_top_highlights convenience function"""
        items = [
            create_test_item(f'item{i}', final_score=1.0-i*0.1)
            for i in range(10)
        ]
        
        highlights = select_top_highlights(items, max_count=3)
        
        assert len(highlights) == 3
        assert highlights[0].item_ref == 'item0'
        assert highlights[1].item_ref == 'item1'
        assert highlights[2].item_ref == 'item2'
    
    def test_select_top_highlights_default_count(self):
        """Test select_top_highlights with default count"""
        items = [
            create_test_item(f'item{i}', final_score=0.8)
            for i in range(10)
        ]
        
        highlights = select_top_highlights(items)
        
        # Default should be 5
        assert len(highlights) == 5
    
    def test_select_top_highlights_with_preferences(self):
        """Test select_top_highlights with preferences"""
        items = [
            create_test_item(f'item{i}')
            for i in range(10)
        ]
        
        prefs = {'topics': ['important']}
        highlights = select_top_highlights(items, max_count=3, user_preferences=prefs)
        
        assert len(highlights) == 3
    
    def test_select_top_highlights_fewer_items(self):
        """Test select_top_highlights with fewer items than requested"""
        items = [
            create_test_item('item1'),
            create_test_item('item2'),
        ]
        
        highlights = select_top_highlights(items, max_count=10)
        
        # Should return all items
        assert len(highlights) == 2


class TestRankerEdgeCases:
    """Test edge cases"""
    
    def test_ranker_with_empty_items(self):
        """Test ranker with empty item list"""
        ranker = Ranker()
        
        ranked = ranker.rank_items([])
        
        assert ranked == []
    
    def test_select_highlights_empty_items(self):
        """Test selecting highlights from empty list"""
        ranker = Ranker()
        
        highlights = ranker.select_top_highlights([])
        
        assert highlights == []
    
    def test_select_items_per_module_empty(self):
        """Test selecting module items from empty list"""
        ranker = Ranker()
        
        selected = ranker.select_items_per_module([], 'email')
        
        assert selected == []
    
    def test_enforce_total_cap_empty(self):
        """Test enforcing cap on empty list"""
        ranker = Ranker()
        
        capped = ranker.enforce_total_cap([])
        
        assert capped == []
    
    def test_ranker_with_zero_scores(self):
        """Test ranker handles items with zero scores"""
        ranker = Ranker()
        
        items = [
            create_test_item('item1', relevance=0.0, urgency=0.0, final_score=0.0),
            create_test_item('item2', relevance=0.0, urgency=0.0, final_score=0.0),
        ]
        
        ranked = ranker.rank_items(items)
        
        assert len(ranked) == 2
    
    def test_select_highlights_with_unranked_items(self):
        """Test selecting highlights automatically ranks items"""
        ranker = Ranker()
        
        items = [
            create_test_item('item1'),
            create_test_item('item2'),
        ]
        # Ensure items are not ranked
        for item in items:
            item.ranking = None
        
        highlights = ranker.select_top_highlights(items, max_count=1)
        
        # Should automatically rank
        assert len(highlights) == 1
        assert highlights[0].ranking is not None
