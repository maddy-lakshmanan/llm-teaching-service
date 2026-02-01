"""Authentication middleware."""

import os
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from ...adapters.auth.firebase_auth import FirebaseAuthService, AuthenticationError


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Firebase authentication.

    Validates Firebase ID tokens on protected routes.
    """

    # Routes that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/health/ready",
        "/health/live",
    }

    def __init__(self, app):
        """Initialize auth middleware."""
        super().__init__(app)
        self.auth_service = FirebaseAuthService()

    async def dispatch(self, request: Request, call_next):
        """
        Process request with authentication.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
            )

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Verify token
            user_info = await self.auth_service.verify_token(token)

            # Add user info to request state
            request.state.user = user_info

            # Continue to next middleware/handler
            response = await call_next(request)
            return response

        except AuthenticationError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
