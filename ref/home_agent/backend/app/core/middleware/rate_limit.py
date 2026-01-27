from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import time
from redis import Redis
from ..config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis as backend."""
    
    def __init__(self, app, redis_client: Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # 1 minute window

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)

        # Get client identifier (IP or API key)
        client_id = self._get_client_identifier(request)
        
        # Check rate limit
        if not await self._check_rate_limit(client_id):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
        
        return await call_next(request)

    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if rate limiting should be skipped for this path."""
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client."""
        # Try to get API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"rate_limit:api:{api_key}"
        
        # Fall back to IP address
        return f"rate_limit:ip:{request.client.host}"

    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        pipe = self.redis.pipeline()
        now = int(time.time())
        window_start = now - self.window
        
        # Remove old requests
        pipe.zremrangebyscore(client_id, 0, window_start)
        
        # Count requests in current window
        pipe.zcard(client_id)
        
        # Add current request
        pipe.zadd(client_id, {str(now): now})
        
        # Set expiry on the set
        pipe.expire(client_id, self.window)
        
        # Execute pipeline
        _, request_count, *_ = pipe.execute()
        
        return request_count < self.rate_limit

class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""
    
    def __init__(self, app, redis_client: Redis):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip API key check for certain paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        # Get and validate API key
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is required"
            )

        if not await self._validate_api_key(api_key):
            raise HTTPException(
                status_code=403,
                detail="Invalid API key"
            )

        return await call_next(request)

    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path."""
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    async def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key against Redis store."""
        key_data = self.redis.hgetall(f"api_key:{api_key}")
        if not key_data:
            return False
            
        # Check if key is active
        return key_data.get(b"active", b"0") == b"1" 