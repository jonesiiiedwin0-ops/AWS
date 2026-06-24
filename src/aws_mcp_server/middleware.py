"""Middleware for the MCP server."""

import time
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = structlog.get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next):
        """Handle requests and catch errors."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(
                "unhandled_error",
                path=request.url.path,
                method=request.method,
                error=str(exc),
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response."""
        start_time = time.time()

        logger.info(
            "request_received",
            method=request.method,
            path=request.url.path,
            client=request.client,
        )

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            "response_sent",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=process_time,
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response
