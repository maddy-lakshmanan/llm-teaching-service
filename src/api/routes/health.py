"""Health check routes."""

from fastapi import APIRouter, Depends

from ...domain.teaching.service import TeachingService
from ..dependencies.services import get_teaching_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.

    Returns service status without dependencies.
    """
    return {"status": "healthy", "service": "llm-teaching-service", "version": "1.0.0"}


@router.get("/health/ready")
async def readiness_check(
    teaching_service: TeachingService = Depends(get_teaching_service),
):
    """
    Readiness check with dependency validation.

    Checks that all required services are available.
    """
    # Check LLM provider health
    try:
        provider = teaching_service.llm_factory.get_provider_for_model()
        health = await provider.health_check()

        return {
            "status": "ready" if health.status == "healthy" else "degraded",
            "service": "llm-teaching-service",
            "version": "1.0.0",
            "dependencies": {
                "llm_provider": {
                    "status": health.status,
                    "response_time_ms": health.response_time_ms,
                }
            },
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": "llm-teaching-service",
            "version": "1.0.0",
            "error": str(e),
        }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.

    Simple check that the service is running.
    """
    return {"status": "alive"}
