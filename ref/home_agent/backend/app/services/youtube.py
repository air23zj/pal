from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException
import googleapiclient.discovery
import os

from ..models.youtube import (
    YouTubeVideo,
    YouTubePlaylist,
    YouTubeWatchRecord,
    YouTubePreference,
    YouTubeRecommendation
)
from ..schemas.youtube import (
    YouTubeVideoCreate,
    YouTubePlaylistCreate,
    YouTubeWatchRecordCreate,
    YouTubePreferenceCreate,
    YouTubeStats,
    YouTubeWatchHistory
)

class YouTubeService:
    def __init__(self, db: Session):
        self.db = db
        self.youtube = googleapiclient.discovery.build(
            'youtube', 'v3',
            developerKey=os.getenv('YOUTUBE_API_KEY')
        )

    def get_video_details(self, video_id: str) -> Optional[YouTubeVideo]:
        """Get video details from YouTube API and store in database."""
        # Check if video exists in database
        video = self.db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == video_id).first()
        if video:
            return video

        # Fetch from YouTube API
        try:
            response = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()

            if not response['items']:
                raise HTTPException(status_code=404, detail="Video not found")

            video_data = response['items'][0]
            snippet = video_data['snippet']
            statistics = video_data['statistics']

            # Create new video record
            video = YouTubeVideo(
                youtube_id=video_id,
                title=snippet['title'],
                description=snippet.get('description'),
                channel_id=snippet['channelId'],
                channel_title=snippet['channelTitle'],
                thumbnail_url=snippet['thumbnails']['high']['url'],
                duration=video_data['contentDetails']['duration'],
                view_count=int(statistics.get('viewCount', 0)),
                like_count=int(statistics.get('likeCount', 0)),
                published_at=snippet['publishedAt'],
                metadata={
                    'tags': snippet.get('tags', []),
                    'category_id': snippet.get('categoryId'),
                    'live_broadcast_content': snippet.get('liveBroadcastContent'),
                    'comment_count': statistics.get('commentCount')
                }
            )

            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            return video

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create_playlist(self, user_id: int, playlist: YouTubePlaylistCreate) -> YouTubePlaylist:
        """Create a new playlist."""
        db_playlist = YouTubePlaylist(
            user_id=user_id,
            **playlist.dict()
        )
        self.db.add(db_playlist)
        self.db.commit()
        self.db.refresh(db_playlist)
        return db_playlist

    def get_playlist(self, user_id: int, playlist_id: int) -> Optional[YouTubePlaylist]:
        """Get a playlist by ID."""
        return self.db.query(YouTubePlaylist)\
            .filter(
                YouTubePlaylist.id == playlist_id,
                YouTubePlaylist.user_id == user_id
            ).first()

    def get_user_playlists(self, user_id: int, skip: int = 0, limit: int = 100) -> List[YouTubePlaylist]:
        """Get all playlists for a user."""
        return self.db.query(YouTubePlaylist)\
            .filter(YouTubePlaylist.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def add_video_to_playlist(self, user_id: int, playlist_id: int, video_id: str) -> YouTubePlaylist:
        """Add a video to a playlist."""
        playlist = self.get_playlist(user_id, playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")

        video = self.get_video_details(video_id)
        if video not in playlist.videos:
            playlist.videos.append(video)
            self.db.commit()
            self.db.refresh(playlist)

        return playlist

    def remove_video_from_playlist(self, user_id: int, playlist_id: int, video_id: int) -> YouTubePlaylist:
        """Remove a video from a playlist."""
        playlist = self.get_playlist(user_id, playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")

        video = self.db.query(YouTubeVideo).get(video_id)
        if video in playlist.videos:
            playlist.videos.remove(video)
            self.db.commit()
            self.db.refresh(playlist)

        return playlist

    def create_watch_record(self, user_id: int, record: YouTubeWatchRecordCreate) -> YouTubeWatchRecord:
        """Create a watch record for a video."""
        db_record = YouTubeWatchRecord(
            user_id=user_id,
            **record.dict()
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def get_watch_history(self, user_id: int, skip: int = 0, limit: int = 50) -> YouTubeWatchHistory:
        """Get user's watch history."""
        records = self.db.query(YouTubeWatchRecord)\
            .filter(YouTubeWatchRecord.user_id == user_id)\
            .order_by(YouTubeWatchRecord.watched_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

        # Get statistics
        stats = self.db.query(
            func.count(YouTubeWatchRecord.id).label('total_videos'),
            func.sum(YouTubeWatchRecord.watch_duration).label('total_duration'),
            func.count(YouTubeWatchRecord.id).filter(YouTubeWatchRecord.completed == True).label('videos_completed')
        ).filter(YouTubeWatchRecord.user_id == user_id).first()

        return YouTubeWatchHistory(
            total_videos=stats.total_videos or 0,
            total_duration=stats.total_duration or 0,
            videos_completed=stats.videos_completed or 0,
            watch_records=records
        )

    def get_or_create_preferences(self, user_id: int) -> YouTubePreference:
        """Get or create user's YouTube preferences."""
        preferences = self.db.query(YouTubePreference)\
            .filter(YouTubePreference.user_id == user_id)\
            .first()

        if not preferences:
            preferences = YouTubePreference(user_id=user_id)
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def update_preferences(self, user_id: int, preferences_update: dict) -> YouTubePreference:
        """Update user's YouTube preferences."""
        preferences = self.get_or_create_preferences(user_id)
        for key, value in preferences_update.items():
            setattr(preferences, key, value)
        self.db.commit()
        self.db.refresh(preferences)
        return preferences

    def get_recommendations(self, user_id: int, limit: int = 10) -> List[YouTubeRecommendation]:
        """Get video recommendations for a user."""
        # Get user's preferences and watch history
        preferences = self.get_or_create_preferences(user_id)
        watch_history = self.get_watch_history(user_id)

        # Get recommended videos based on watch history and preferences
        recommendations = self.db.query(YouTubeRecommendation)\
            .filter(
                YouTubeRecommendation.user_id == user_id,
                YouTubeRecommendation.is_dismissed == False
            )\
            .order_by(YouTubeRecommendation.score.desc())\
            .limit(limit)\
            .all()

        # If not enough recommendations, generate new ones
        if len(recommendations) < limit:
            self._generate_recommendations(user_id, preferences, watch_history)
            recommendations = self.db.query(YouTubeRecommendation)\
                .filter(
                    YouTubeRecommendation.user_id == user_id,
                    YouTubeRecommendation.is_dismissed == False
                )\
                .order_by(YouTubeRecommendation.score.desc())\
                .limit(limit)\
                .all()

        return recommendations

    def _generate_recommendations(self, user_id: int, preferences: YouTubePreference, watch_history: YouTubeWatchHistory):
        """Generate new recommendations based on user preferences and watch history."""
        # Implementation would depend on recommendation algorithm
        # Could use YouTube API recommendations, collaborative filtering, etc.
        pass

    def get_stats(self, user_id: int) -> YouTubeStats:
        """Get YouTube statistics for a user."""
        now = datetime.utcnow()
        stats = self.db.query(
            func.count(YouTubeWatchRecord.id).label('total_videos'),
            func.sum(YouTubeWatchRecord.watch_duration).label('total_duration'),
            func.count(YouTubeWatchRecord.id).filter(YouTubeWatchRecord.completed == True).label('completed')
        ).filter(YouTubeWatchRecord.user_id == user_id).first()

        # Get playlist count
        playlist_count = self.db.query(func.count(YouTubePlaylist.id))\
            .filter(YouTubePlaylist.user_id == user_id)\
            .scalar()

        # Get channel stats
        channel_stats = self.db.query(
            YouTubeVideo.channel_id,
            YouTubeVideo.channel_title,
            func.count(YouTubeWatchRecord.id).label('count')
        ).join(YouTubeWatchRecord)\
            .filter(YouTubeWatchRecord.user_id == user_id)\
            .group_by(YouTubeVideo.channel_id, YouTubeVideo.channel_title)\
            .all()

        # Get popular videos
        popular_videos = self.db.query(
            YouTubeVideo.youtube_id,
            YouTubeVideo.title,
            func.count(YouTubeWatchRecord.id).label('count')
        ).join(YouTubeWatchRecord)\
            .filter(YouTubeWatchRecord.user_id == user_id)\
            .group_by(YouTubeVideo.youtube_id, YouTubeVideo.title)\
            .order_by(func.count(YouTubeWatchRecord.id).desc())\
            .limit(10)\
            .all()

        # Get watch time by day for the last 30 days
        watch_time_by_day = {}
        for i in range(30):
            date = (now - timedelta(days=i)).date()
            duration = self.db.query(func.sum(YouTubeWatchRecord.watch_duration))\
                .filter(
                    YouTubeWatchRecord.user_id == user_id,
                    func.date(YouTubeWatchRecord.watched_at) == date
                ).scalar() or 0
            watch_time_by_day[date.isoformat()] = duration

        return YouTubeStats(
            total_playlists=playlist_count,
            total_videos_watched=stats.total_videos or 0,
            total_watch_time=stats.total_duration or 0,
            videos_completed=stats.completed or 0,
            average_completion_rate=stats.completed / stats.total_videos if stats.total_videos else 0,
            by_channel={cs.channel_id: cs.count for cs in channel_stats},
            by_category={},  # Would need to implement category tracking
            popular_videos=[{
                'video_id': pv.youtube_id,
                'title': pv.title,
                'count': pv.count
            } for pv in popular_videos],
            watch_time_by_day=watch_time_by_day
        ) 