"""
Summarization API endpoints for search and YouTube.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.summarization import perform_search, summarize_youtube_video

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for search summarization"""
    query: str
    search_engine: str = "serper"


class YouTubeRequest(BaseModel):
    """Request model for YouTube summarization"""
    url: str


class SearchResponse(BaseModel):
    """Response model for search summarization"""
    answer: str
    sources: List[Dict[str, str]]
    related_questions: List[str]


class YouTubeResponse(BaseModel):
    """Response model for YouTube summarization"""
    summary: str
    video_id: Optional[str] = None
    url: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest) -> SearchResponse:
    """
    Perform search and return summarized results with sources and related questions.

    Args:
        request: Search request with query and engine

    Returns:
        Search response with answer, sources, and related questions
    """
    try:
        logger.info(f"Performing search for query: {request.query}")

        result = await perform_search(request.query, request.search_engine)

        return SearchResponse(
            answer=result["answer"],
            sources=result["sources"],
            related_questions=result["related_questions"]
        )

    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/youtube/summarize", response_model=YouTubeResponse)
async def youtube_summarize_endpoint(request: YouTubeRequest) -> YouTubeResponse:
    """
    Summarize a YouTube video using its transcript.

    Args:
        request: YouTube request with video URL

    Returns:
        Dictionary with summary, metadata, and video information
    """
    try:
        logger.info(f"Summarizing YouTube video: {request.url}")

        result = await summarize_youtube_video(request.url)

        return result

    except Exception as e:
        logger.error(f"YouTube summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"YouTube summarization failed: {str(e)}")