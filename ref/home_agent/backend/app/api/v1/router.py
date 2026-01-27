from fastapi import APIRouter

from .endpoints import (
    auth,
    documents,
    health,
    travel,
    weather,
    voice_memos,
    video,
    photos,
    rooms,
    news,
    deals,
    search,
    youtube
)

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(travel.router, prefix="/travel", tags=["Travel"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(voice_memos.router, prefix="/voice-memos", tags=["Voice Memos"])
api_router.include_router(video.router, prefix="/video", tags=["Video"])
api_router.include_router(photos.router, prefix="/photos", tags=["Photos"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(news.router, prefix="/news", tags=["News"])
api_router.include_router(deals.router, prefix="/deals", tags=["Deals"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["YouTube"]) 