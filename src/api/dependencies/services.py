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
    from ..dependencies.container import Container

    container: Container = request.app.state.container
    from ...domain.teaching.service import TeachingService
    from typing import cast

    return cast(TeachingService, container.teaching_service)
