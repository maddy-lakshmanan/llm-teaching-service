"""Unit tests for cache service."""

import pytest
from src.adapters.cache.redis_cache import InMemoryCacheService
from src.core.models import TeachingRequest, TeachingResponse, Subject, GradeLevel


@pytest.mark.asyncio
async def test_cache_set_and_get():
    """Test setting and getting cached responses."""
    cache = InMemoryCacheService()

    request = TeachingRequest(
        student_id="test-123",
        question="What is 2+2?",
        subject=Subject.MATH,
        grade_level=GradeLevel.ELEMENTARY,
    )

    response = TeachingResponse(
        answer="4",
        model_used="phi3-mini",
        tokens_used=10,
        estimated_cost=0.00001,
        confidence=0.95,
        processing_time_ms=100,
    )

    # Set in cache
    await cache.set_teaching_response(request, response)

    # Get from cache
    cached = await cache.get_teaching_response(request)

    assert cached is not None
    assert cached.answer == "4"
    assert cached.model_used == "phi3-mini"


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss returns None."""
    cache = InMemoryCacheService()

    request = TeachingRequest(
        student_id="test-456",
        question="What is photosynthesis?",
        subject=Subject.SCIENCE,
        grade_level=GradeLevel.MIDDLE_SCHOOL,
    )

    # Should return None for cache miss
    cached = await cache.get_teaching_response(request)
    assert cached is None


@pytest.mark.asyncio
async def test_cache_invalidation():
    """Test cache invalidation."""
    cache = InMemoryCacheService()

    request = TeachingRequest(
        student_id="test-789",
        question="Test question",
        subject=Subject.MATH,
        grade_level=GradeLevel.HIGH_SCHOOL,
    )

    response = TeachingResponse(
        answer="Test answer",
        model_used="phi3-mini",
        tokens_used=20,
        estimated_cost=0.00002,
        confidence=0.9,
        processing_time_ms=150,
    )

    await cache.set_teaching_response(request, response)

    # Invalidate
    deleted = await cache.invalidate_cache("teaching:math:*")

    assert deleted >= 1


@pytest.mark.asyncio
async def test_cache_stats():
    """Test cache statistics."""
    cache = InMemoryCacheService()

    # Initial stats
    stats = await cache.get_cache_stats()
    assert stats["hit_count"] == 0
    assert stats["miss_count"] == 0

    request = TeachingRequest(
        student_id="test-abc",
        question="Cache test",
        subject=Subject.MATH,
        grade_level=GradeLevel.ELEMENTARY,
    )

    # Miss
    await cache.get_teaching_response(request)

    # Set
    response = TeachingResponse(
        answer="Test",
        model_used="phi3-mini",
        tokens_used=5,
        estimated_cost=0.000005,
        confidence=0.8,
        processing_time_ms=50,
    )
    await cache.set_teaching_response(request, response)

    # Hit
    await cache.get_teaching_response(request)

    # Check stats
    stats = await cache.get_cache_stats()
    assert stats["hit_count"] == 1
    assert stats["miss_count"] == 1
