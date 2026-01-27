"""
YouTube summarization utilities borrowed from home_agent.
"""
import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter

from openai import AsyncOpenAI

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize OpenAI client lazily
client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        client = AsyncOpenAI(api_key=api_key)
    return client


def extract_video_id(url: str) -> str:
    """
    Extract video ID from YouTube URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID string
    """
    # Handle different YouTube URL formats
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        if parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        if parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    raise ValueError("Invalid YouTube URL")


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def get_transcript(video_id: str) -> list:
    """
    Get transcript from YouTube video.

    Args:
        video_id: YouTube video ID

    Returns:
        List of transcript entries with timestamps
    """
    try:
        # Try with proxy support if available
        if HTTPX_AVAILABLE:
            # Check for proxy configuration
            proxy_url = os.getenv('YOUTUBE_PROXY_URL') or os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')

            if proxy_url:
                logger.info(f"Using proxy for YouTube transcript: {proxy_url}")
                # Create httpx client with proxy
                http_client = httpx.Client(
                    proxies={
                        "http://": proxy_url,
                        "https://": proxy_url
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                    timeout=30.0
                )
                api = YouTubeTranscriptApi(http_client=http_client)
            else:
                logger.info("No proxy configured, using direct connection")
                api = YouTubeTranscriptApi()
        else:
            logger.warning("httpx not available, using direct connection without proxy support")
            api = YouTubeTranscriptApi()

        transcript_list = api.fetch(video_id)
        # Convert to dict format for compatibility with existing code
        return [{"text": entry.text, "start": entry.start, "duration": entry.duration} for entry in transcript_list]
    except Exception as e:
        logger.error(f"YouTube transcript fetch failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Could not get transcript: {str(e)}")


async def get_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Get video metadata from YouTube Data API v3.

    Args:
        video_id: YouTube video ID

    Returns:
        Dictionary with video metadata or None if API unavailable
    """
    if not YOUTUBE_API_AVAILABLE:
        return None

    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return None

        youtube = build('youtube', 'v3', developerKey=api_key)

        # Get video details
        request = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=video_id
        )
        response = request.execute()

        if not response['items']:
            return None

        video = response['items'][0]
        snippet = video['snippet']
        statistics = video.get('statistics', {})
        content_details = video.get('contentDetails', {})

        return {
            'title': snippet.get('title', ''),
            'channel_title': snippet.get('channelTitle', ''),
            'description': snippet.get('description', '')[:200] + '...' if snippet.get('description') else '',
            'published_at': snippet.get('publishedAt', ''),
            'duration': content_details.get('duration', ''),
            'view_count': statistics.get('viewCount', '0'),
            'like_count': statistics.get('likeCount', '0'),
            'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', '')
        }

    except Exception as e:
        logger.warning(f"Could not get video metadata: {e}")
        return None


async def summarize_youtube_video(url: str) -> Dict[str, Any]:
    """
    Summarize a YouTube video using its transcript.

    Args:
        url: YouTube video URL

    Returns:
        Dictionary with summary, metadata, and video information
    """
    try:
        # Extract video ID from URL
        video_id = extract_video_id(url)

        # Get video metadata (optional)
        metadata = await get_video_metadata(video_id)

        # Get video transcript with timestamps
        transcript_list = get_transcript(video_id)

        # Process transcript with timestamps
        processed_entries = []
        for entry in transcript_list:
            timestamp = format_timestamp(entry["start"])
            text = entry["text"].strip()  # Ensure text is stripped of whitespace
            processed_entries.append(f"{text} [{timestamp}]")  # Add timestamp as citation

        text = "\n\n".join(processed_entries)  # Use double newlines for better separation

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,  # Reduced chunk size to leave room for timestamps
            chunk_overlap=1000,  # Increased overlap to prevent cutting off context
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Added period+space as separator
        )
        chunks = text_splitter.split_text(text)

        # Ensure timestamps aren't cut off at chunk boundaries
        for i in range(len(chunks)):
            # If chunk ends with an incomplete timestamp, find the last complete timestamp
            if '[' in chunks[i] and ']' not in chunks[i].split('[')[-1]:
                last_complete = chunks[i].rindex(']')
                if i + 1 < len(chunks):
                    # Move the incomplete part to the next chunk
                    chunks[i + 1] = chunks[i][last_complete + 1:] + chunks[i + 1]
                    chunks[i] = chunks[i][:last_complete + 1]

        # Generate summary for each chunk
        summaries = []
        failed_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                response = await get_openai_client().chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that creates clear, well-structured summaries of YouTube video segments. For each key point or quote you mention, you MUST include the timestamp citation in [HH:MM:SS] format at the end of the sentence. If multiple points occur in sequence, combine their timestamps with a hyphen, like [HH:MM:SS-HH:MM:SS]. Keep the summary focused on key points and maintain chronological order. Keep the summary to 500 words or less."
                        },
                        {
                            "role": "user",
                            "content": f"Please summarize this segment of the transcript, making sure to cite timestamps for each key point. For sequential points, combine their timestamps with a hyphen [HH:MM:SS-HH:MM:SS]. Each point must have a timestamp citation at the end of its sentence. Never cut off timestamps:\n\n{chunk}"
                        }
                    ],
                    temperature=0.7
                )
                summaries.append(response.choices[0].message.content)
            except Exception as e:
                logger.error(f"Error summarizing chunk {i}: {str(e)}")
                failed_chunks.append(i)
                continue

        if not summaries:
            raise HTTPException(status_code=500, detail="Failed to generate summary")

        if failed_chunks:
            logger.warning(f"Failed to summarize chunks: {failed_chunks}")

        # Generate a final, cohesive summary
        combined_summary = "\n\n".join(summaries)
        final_response = await get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates clear, well-structured final summaries of YouTube videos. Your task is to take multiple segment summaries and create a cohesive, chronological summary that PRESERVES ALL TIMESTAMP CITATIONS. For sequential points, combine their timestamps with a hyphen [HH:MM:SS-HH:MM:SS]. Keep the summary to 500 words or less. Format the summary in markdown with sections and bullet points. Never cut off or omit any timestamps. "
                },
                {
                    "role": "user",
                    "content": f"Create a final, cohesive summary from these segment summaries. Maintain chronological order and PRESERVE ALL TIMESTAMP CITATIONS. For sequential points or related ideas, combine their timestamps with a hyphen [HH:MM:SS-HH:MM:SS]. If you notice any gaps in the timeline, please note them:\n\n{combined_summary}"
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )

        final_summary = final_response.choices[0].message.content.strip()

        return {
            'summary': final_summary,
            'video_id': video_id,
            'url': url,
            'metadata': metadata
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error summarizing YouTube video: {error_msg}")

        # Check for different types of errors
        error_lower = error_msg.lower()

        if "ipblocked" in error_lower or "ip blocked" in error_lower:
            return {
                'summary': f"""# YouTube Video Summary: {url}

## 🚫 IP Blocked by YouTube

❌ **YouTube is blocking requests from your IP address.**

This happens when:
- Too many requests have been made recently
- You're using a cloud/server IP (AWS, GCP, etc.)
- Your IP has been temporarily blocked

## Solutions:
1. **Wait 1-2 hours** and try again
2. **Use a VPN** to change your IP address
3. **Use a proxy server** for requests
4. **Try from a different network**

## Test Videos:
Try these videos that usually work:
- https://www.youtube.com/watch?v=dQw4w9WgXcQ (Rickroll)
- https://www.youtube.com/watch?v=jNQXAC9IVRw (Short video)
- Any video with CC (closed captions) enabled

*Error: IP blocked by YouTube*""",
                'video_id': video_id,
                'url': url,
                'metadata': metadata,
                'error_type': 'ip_blocked'
            }
        elif "videounavailable" in error_lower or "video unavailable" in error_lower:
            return {
                'summary': f"""# YouTube Video Summary: {url}

## Video Unavailable

❌ **This video is not available or has been removed.**

Possible reasons:
- Video was deleted
- Video is private
- Video is age-restricted
- Invalid video URL

Please check the URL and try again.

*Error: Video unavailable*""",
                'video_id': video_id,
                'url': url,
                'metadata': metadata,
                'error_type': 'video_unavailable'
            }
        elif "transcript" in error_lower or "subtitles" in error_lower:
            return {
                'summary': f"""# YouTube Video Summary: {url}

## Transcript Not Available

❌ **This video doesn't have transcripts/subtitles enabled.**

YouTube summarization requires videos with:
- Automatic captions (CC)
- Manual subtitles
- Creator-provided transcripts

## Try These Instead:
- TED Talks (usually have transcripts)
- Educational content
- Tech conference videos
- Videos with CC (closed captions) enabled

## Alternative Option:
Use the **Web Search** feature to search for video summaries or transcripts from other sources.

*Error: No transcripts available*""",
                'video_id': video_id,
                'url': url,
                'metadata': metadata,
                'error_type': 'transcript_unavailable'
            }
        else:
            # Return error for other API failures (OpenAI, etc.)
            return {
                'summary': f"""# YouTube Video Summary: {url}

## Processing Error

❌ **AI summarization failed.**

This could be due to:
- OpenAI API issues
- Network connectivity
- API rate limits

## Try Again Later:
Please check your API keys and try again.

*Error: {error_msg}*""",
                'video_id': extract_video_id(url) if 'url' in locals() else None,
                'url': url,
                'metadata': await get_video_metadata(extract_video_id(url)) if 'url' in locals() else None,
                'error_type': 'processing_error'
            }