"""
Core functionality tests that verify the actual codebase works
"""
import pytest
from datetime import datetime, timezone
from packages.normalizer.normalizer import Normalizer, normalize_social_posts
from packages.ranking.ranker import Ranker  
from packages.memory.fingerprint import generate_fingerprint, content_hash
from packages.memory.novelty import NoveltyDetector
from packages.memory.memory_manager import MemoryManager
from packages.database import crud


class TestNormalizer:
    """Test normalizer with correct API"""
    
    def test_normalize_social_post(self):
        """Test social post normalization - this one works!"""
        post_data = {
            'id': 'post123',
            'author': 'testuser',
            'content': 'Test post content',
            'timestamp': '2024-01-15T12:00:00Z',
            'url': 'https://example.com/post123',
            'metrics': {'likes': 100}
        }
        
        result = Normalizer.normalize_social_post(post_data, 'x')
        
        assert result.source == 'x'
        assert result.type == 'social_post'
        assert 'testuser' in result.title
        
    def test_normalize_gmail_with_source_id(self):
        """Test Gmail normalization with correct source_id format"""
        gmail_data = {
            'source_id': 'msg123',
            'snippet': 'Test email content',
            'subject': 'Test Subject',
            'from': 'test@example.com',
            'timestamp_utc': '2024-01-15T12:00:00Z'
        }
        
        result = Normalizer.normalize_gmail_item(gmail_data)
        
        assert result.source == 'gmail'
        assert result.type == 'email'
        assert 'Test Subject' in result.title
        
    def test_normalize_calendar_with_source_id(self):
        """Test Calendar normalization with correct source_id format"""
        calendar_data = {
            'source_id': 'event123',
            'title': 'Team Meeting',
            'summary': 'Weekly team sync',
            'start_time': '2024-01-15T14:00:00Z',
            'end_time': '2024-01-15T15:00:00Z',
            'timestamp_utc': '2024-01-15T14:00:00Z'
        }
        
        result = Normalizer.normalize_calendar_item(calendar_data)
        
        assert result.source == 'calendar'
        assert result.type == 'event'
        assert 'Team Meeting' in result.title
        
    def test_generate_stable_id(self):
        """Test stable ID generation"""
        id1 = Normalizer.generate_stable_id('gmail', 'email', 'msg123')
        id2 = Normalizer.generate_stable_id('gmail', 'email', 'msg123')
        
        # IDs should be consistent
        assert id1 == id2
        # ID should contain source
        assert 'gmail' in id1.lower() or 'item_gmail' in id1


class TestRanking:
    """Test ranking system"""
    
    def test_ranker_basic(self):
        """Test that ranker can process items"""
        from packages.shared.schemas import BriefItem, NoveltyInfo, RankingScores
        
        item = BriefItem(
            item_ref='test_1',
            source='gmail',
            type='email',
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            title='Test',
            summary='Test',
            why_it_matters='Test',
            entities=[],
            novelty=NoveltyInfo(
                label='NEW',
                reason='First',
                first_seen_utc=datetime.now(timezone.utc).isoformat()
            ),
            ranking=RankingScores(
                relevance_score=0.5,
                urgency_score=0.5,
                credibility_score=0.5,
                actionability_score=0.5,
                final_score=0.5
            ),
            evidence=[],
            suggested_actions=[]
        )
        
        ranker = Ranker()
        ranked = ranker.rank_items([item])
        
        assert len(ranked) == 1
        assert ranked[0].ranking.final_score > 0


class TestMemory:
    """Test memory and fingerprinting"""
    
    def test_content_hash(self):
        """Test content hash generation"""
        item_dict = {
            'source': 'gmail',
            'type': 'email',
            'title': 'Test',
            'summary': 'Test summary'
        }
        
        hash_val = content_hash(item_dict)
        
        assert isinstance(hash_val, str)
        assert len(hash_val) > 0
        
    def test_generate_fingerprint(self):
        """Test fingerprint generation with correct signature"""
        # generate_fingerprint takes (source, item_type, item_data)
        item_data = {
            'id': 'test123',
            'title': 'Test',
            'content': 'Test content'
        }
        
        fp = generate_fingerprint('gmail', 'email', item_data)
        
        assert isinstance(fp, str)
        assert len(fp) > 0
        
    def test_novelty_detector_init(self):
        """Test NoveltyDetector initialization"""
        # Check what parameters it actually takes
        detector = NoveltyDetector()
        
        assert detector is not None
        
    def test_memory_manager(self, tmp_path):
        """Test MemoryManager initialization"""
        from pathlib import Path
        manager = MemoryManager(memory_dir=Path(tmp_path))
        
        assert manager is not None


class TestDatabase:
    """Test database operations"""
    
    def test_database_connection(self, db_session):
        """Test database session works"""
        assert db_session is not None
        
    def test_get_or_create_user(self, db_session):
        """Test user creation with correct API"""
        user = crud.get_or_create_user(
            db_session,
            user_id='test_user_123',
            timezone='UTC'
        )
        
        assert user is not None
        assert user.id == 'test_user_123'
        
    def test_create_brief_run(self, db_session):
        """Test creating a brief run"""
        # First create a user
        user = crud.get_or_create_user(db_session, 'test_user_123')
        
        run = crud.create_brief_run(
            db_session,
            user_id=user.id,
            since_timestamp=datetime.now(timezone.utc),
            status='queued'
        )
        
        assert run is not None
        assert run.user_id == user.id
        assert run.status == 'queued'
        
    def test_feedback_event(self, db_session):
        """Test creating feedback event"""
        # Create user first
        user = crud.get_or_create_user(db_session, 'test_user_123')
        
        # Create item
        from packages.shared.schemas import BriefItem, NoveltyInfo, RankingScores
        
        item = BriefItem(
            item_ref='test_item_1',
            source='gmail',
            type='email',
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            title='Test',
            summary='Test',
            why_it_matters='Test',
            entities=[],
            novelty=NoveltyInfo(
                label='NEW',
                reason='First',
                first_seen_utc=datetime.now(timezone.utc).isoformat()
            ),
            ranking=RankingScores(
                relevance_score=0.5,
                urgency_score=0.5,
                credibility_score=0.5,
                actionability_score=0.5,
                final_score=0.5
            ),
            evidence=[],
            suggested_actions=[]
        )
        
        db_item = crud.create_or_update_item(
            db_session,
            item_id=item.item_ref,
            user_id=user.id,
            source=item.source,
            type=item.type,
            timestamp=datetime.fromisoformat(item.timestamp_utc),
            title=item.title,
            summary=item.summary
        )
        
        # Create feedback event
        event = crud.create_feedback_event(
            db_session,
            user_id=user.id,
            item_id=db_item.id,
            event_type='clicked',
            payload={'test': 'data'}
        )
        
        assert event is not None
        assert event.user_id == user.id
        assert event.event_type == 'clicked'


class TestIntegration:
    """Integration tests across components"""
    
    def test_end_to_end_social_post(self):
        """Test complete flow for social post"""
        # 1. Normalize
        post = {
            'id': 'post_end_to_end',
            'author': 'testuser',
            'content': 'Integration test post',
            'timestamp': '2024-01-15T12:00:00Z',
            'url': 'https://example.com/post',
            'metrics': {'likes': 50}
        }
        
        brief_item = Normalizer.normalize_social_post(post, 'x')
        assert brief_item is not None
        
        # 2. Generate fingerprint
        fp = generate_fingerprint('x', 'social_post', post)
        assert isinstance(fp, str)
        
        # 3. Hash content
        hash_val = content_hash(post)
        assert isinstance(hash_val, str)
        
        # 4. Rank
        ranker = Ranker()
        ranked = ranker.rank_items([brief_item])
        assert len(ranked) == 1
        assert ranked[0].ranking.final_score > 0
        
        print("✅ End-to-end test passed!")
