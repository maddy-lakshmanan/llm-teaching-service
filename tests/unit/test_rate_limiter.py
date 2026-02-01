"""Unit tests for rate limiter."""

import asyncio

import pytest

from src.domain.rate_limit.rate_limiter import InMemoryRateLimiter, RateLimitExceeded


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests():
    """Test that rate limiter allows requests within limit."""
    limiter = InMemoryRateLimiter()

    # Should allow up to limit
    for i in range(5):
        allowed = await limiter.check_limit("user-123", limit=10, window_seconds=60)
        assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_blocks_excess():
    """Test that rate limiter blocks requests over limit."""
    limiter = InMemoryRateLimiter()

    # Use up the limit
    for i in range(10):
        await limiter.check_limit("user-456", limit=10, window_seconds=60)

    # Next request should be blocked
    with pytest.raises(RateLimitExceeded):
        await limiter.check_limit("user-456", limit=10, window_seconds=60)


@pytest.mark.asyncio
async def test_rate_limiter_per_user():
    """Test that rate limiting is per user."""
    limiter = InMemoryRateLimiter()

    # User 1 uses their limit
    for i in range(10):
        await limiter.check_limit("user-1", limit=10, window_seconds=60)

    # User 2 should still be able to make requests
    allowed = await limiter.check_limit("user-2", limit=10, window_seconds=60)
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_window():
    """Test that rate limiter window resets."""
    limiter = InMemoryRateLimiter()

    # Use up limit with short window
    for i in range(5):
        await limiter.check_limit("user-789", limit=5, window_seconds=1)

    # Should be blocked
    with pytest.raises(RateLimitExceeded):
        await limiter.check_limit("user-789", limit=5, window_seconds=1)

    # Wait for window to reset
    await asyncio.sleep(1.1)

    # Should be allowed again
    allowed = await limiter.check_limit("user-789", limit=5, window_seconds=1)
    assert allowed is True


@pytest.mark.asyncio
async def test_get_remaining():
    """Test getting remaining requests."""
    limiter = InMemoryRateLimiter()

    # Make 3 requests
    for i in range(3):
        await limiter.check_limit("user-abc", limit=10, window_seconds=60)

    # Should have 7 remaining
    remaining = await limiter.get_remaining("user-abc", limit=10, window_seconds=60)
    assert remaining == 7


@pytest.mark.asyncio
async def test_reset_limit():
    """Test resetting rate limit."""
    limiter = InMemoryRateLimiter()

    # Use up limit
    for i in range(10):
        await limiter.check_limit("user-reset", limit=10, window_seconds=60)

    # Reset
    await limiter.reset_limit("user-reset")

    # Should be able to make requests again
    allowed = await limiter.check_limit("user-reset", limit=10, window_seconds=60)
    assert allowed is True
