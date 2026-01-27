from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from loguru import logger
import time

from .core.config import settings
from .core.cache import init_cache, CacheManager
from .core.exceptions import setup_exception_handlers
from .core.middleware.logging import RequestLoggingMiddleware, ResponseHeaderMiddleware
from .core.middleware.rate_limit import RateLimitMiddleware, APIKeyMiddleware
from .core.websocket import ConnectionManager

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.SHOW_API_DOCS else None,
    redoc_url="/redoc" if settings.SHOW_API_DOCS else None,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ResponseHeaderMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
app.add_middleware(APIKeyMiddleware, redis_client=redis_client)

# Setup exception handlers
setup_exception_handlers(app)

# Initialize WebSocket manager
ws_manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Initialize cache
        await init_cache()
        logger.info("Cache initialized")
        
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection established")
        
        # Additional startup tasks...
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        # Close Redis connections
        CacheManager.close()
        redis_client.close()
        logger.info("Connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION
    }

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    return {
        "uptime": time.time() - app.state.start_time,
        "websocket_connections": ws_manager.get_connection_stats(),
        "redis_connected": redis_client.ping()
    }

# Import and include API routers
from .api.v1.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Store startup time
app.state.start_time = time.time()
