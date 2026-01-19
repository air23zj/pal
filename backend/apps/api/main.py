"""
Morning Brief AGI - FastAPI Backend
Main API server entry point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import brief, feedback, health


# CORS configuration from environment
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Morning Brief API starting up...")
    yield
    # Shutdown
    print("👋 Morning Brief API shutting down...")


app = FastAPI(
    title="Morning Brief AGI API",
    description="Intelligent morning briefing system API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - configurable via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(brief.router, prefix="/api/brief", tags=["brief"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Morning Brief AGI API",
        "version": "0.1.0",
        "status": "running",
    }
