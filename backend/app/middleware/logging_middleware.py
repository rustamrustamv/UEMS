"""
Logging middleware that injects request context into all logs.
"""

import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request context to logs and track request duration.
    Automatically injects: request_id, user_id, method, path, client_ip
    """

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract user_id from JWT if available (set by auth dependency)
        user_id = getattr(request.state, 'user_id', None)

        # Create log context
        extra = {
            'request_id': request_id,
            'user_id': user_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': request.client.host if request.client else 'unknown'
        }

        # Record start time
        start_time = time.time()

        logger.info(
            "Request started",
            extra={**extra, 'event': 'request_started'}
        )

        try:
            # Process request
            response = await call_next(request)
            duration = time.time() - start_time

            logger.info(
                "Request completed",
                extra={
                    **extra,
                    'event': 'request_completed',
                    'status_code': response.status_code,
                    'duration_seconds': round(duration, 3)
                }
            )

            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            return response

        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    **extra,
                    'event': 'request_failed',
                    'error_type': type(exc).__name__,
                    'error_message': str(exc),
                    'duration_seconds': round(duration, 3)
                },
                exc_info=True
            )
            raise
