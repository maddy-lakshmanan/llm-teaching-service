"""Service dependencies for FastAPI."""

from fastapi import Request
from ...domain.teaching.service import TeachingService


async def get_teaching_service(request: Request) -> TeachingService:
    """
    Get teaching service from container.

    Args:
        request: FastAPI request with container in state

    Returns:
        TeachingService instance
    """
    container = request.app.state.container
    return container.teaching_service
