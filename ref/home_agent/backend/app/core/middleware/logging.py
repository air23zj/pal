import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import json
from typing import Callable

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Start timer
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            await self._log_response(response, request_id, process_time)
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(f"Request {request_id} failed after {process_time:.4f}s: {str(e)}")
            raise

    async def _log_request(self, request: Request, request_id: str):
        """Log request details."""
        # Get request body (if any)
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                body = await request.body()

        logger.info(
            "Request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "headers": dict(request.headers),
                "body": body,
                "query_params": dict(request.query_params),
                "path_params": dict(request.path_params)
            }
        )

    async def _log_response(self, response: Response, request_id: str, process_time: float):
        """Log response details."""
        # Get response body (if any)
        body = None
        if hasattr(response, "body"):
            try:
                body = json.loads(response.body.decode())
            except:
                body = response.body.decode()

        logger.info(
            "Response",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body,
                "process_time": f"{process_time:.4f}s"
            }
        )

class ResponseHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware for adding standard response headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response 