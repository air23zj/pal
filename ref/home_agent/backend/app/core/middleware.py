from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
from ..config import settings

class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request timing."""
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="clarity_session",
        max_age=settings.SESSION_MAX_AGE
    )

    # Request timing middleware
    app.add_middleware(RequestTimingMiddleware)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    def __init__(
        self,
        app: FastAPI,
        calls: int = 100,
        period: int = 60
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.cache = {}

    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # Clean old entries
        self.cache = {
            ip: timestamps 
            for ip, timestamps in self.cache.items() 
            if timestamps[-1] > current_time - self.period
        }

        # Check rate limit
        if client_ip in self.cache:
            timestamps = self.cache[client_ip]
            if len(timestamps) >= self.calls:
                oldest = timestamps[0]
                if current_time - oldest < self.period:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests"}
                    )
                timestamps.pop(0)
            timestamps.append(current_time)
        else:
            self.cache[client_ip] = [current_time]

        return await call_next(request)
