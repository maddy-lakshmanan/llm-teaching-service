"""Admin API routes."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from ...domain.teaching.service import TeachingService
from ..dependencies.services import get_teaching_service


router = APIRouter()


@router.get("/models")
async def list_models(
    teaching_service: TeachingService = Depends(get_teaching_service),
):
    """
    List available LLM models.

    Returns:
        List of configured models with metadata
    """
    models = teaching_service.llm_factory.config.list_available_models()

    model_details = []
    for model_id in models:
        config = teaching_service.llm_factory.config.get_model_config(model_id)
        model_details.append(
            {
                "id": model_id,
                "provider": config.provider,
                "model_name": config.model_name,
                "max_tokens": config.max_tokens,
                "cost_per_1k_tokens": config.cost_per_1k_tokens,
            }
        )

    return {
        "models": model_details,
        "default": teaching_service.llm_factory.config.default_model,
    }


@router.get("/cache/stats")
async def get_cache_stats(
    teaching_service: TeachingService = Depends(get_teaching_service),
):
    """
    Get cache performance statistics.

    Returns:
        Cache stats including hit rate, size, etc.
    """
    try:
        stats = await teaching_service.cache.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve cache stats: {str(e)}"
        )


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: str, teaching_service: TeachingService = Depends(get_teaching_service)
):
    """
    Invalidate cache entries matching pattern.

    Args:
        pattern: Redis key pattern (e.g., "teaching:math:*")

    Returns:
        Number of keys deleted
    """
    try:
        deleted = await teaching_service.cache.invalidate_cache(pattern)
        return {"pattern": pattern, "deleted": deleted, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.get("/usage/summary")
async def get_usage_summary(
    teaching_service: TeachingService = Depends(get_teaching_service),
):
    """
    Get overall usage summary.

    Returns:
        Aggregated usage metrics across all users
    """
    try:
        summary = await teaching_service.database.get_usage_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve usage summary: {str(e)}"
        )
