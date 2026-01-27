from fastapi import APIRouter
from .endpoints import (
    auth,
    users,
    health,
    weather,
    voice_memo,
    video_call,
    photo,
    document,
    news,
    search,
    youtube,
    shopping,
    utilities
)

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User routes
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Health routes
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Weather routes
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])

# Voice memo routes
api_router.include_router(voice_memo.router, prefix="/voice-memos", tags=["Voice Memos"])

# Video call routes
api_router.include_router(video_call.router, prefix="/video-calls", tags=["Video Calls"])

# Photo routes
api_router.include_router(photo.router, prefix="/photos", tags=["Photos"])

# Document routes
api_router.include_router(document.router, prefix="/documents", tags=["Documents"])

# News routes
api_router.include_router(news.router, prefix="/news", tags=["News"])

# Search routes
api_router.include_router(search.router, prefix="/search", tags=["Search"])

# YouTube routes
api_router.include_router(youtube.router, prefix="/youtube", tags=["YouTube"])

# Shopping routes
api_router.include_router(shopping.router, prefix="/shopping", tags=["Shopping"])

# Utilities routes
api_router.include_router(utilities.router, prefix="/utilities", tags=["Utilities"]) 