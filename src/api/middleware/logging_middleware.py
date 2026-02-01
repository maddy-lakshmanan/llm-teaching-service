"""Logging middleware."""

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging.

    Logs all requests with timing, status codes, and request IDs.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request with logging.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} | "
            f"request_id={request_id}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} | "
                f"status={response.status_code} | "
                f"duration_ms={duration_ms} | "
                f"request_id={request_id}"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} | "
                f"error={str(e)} | "
                f"duration_ms={duration_ms} | "
                f"request_id={request_id}"
            )

            raise
