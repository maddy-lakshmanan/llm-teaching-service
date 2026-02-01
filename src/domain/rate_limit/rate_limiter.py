"""Redis-based rate limiter implementation."""

import time
from redis.asyncio import Redis
from ...core.ports import AbstractRateLimiter


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception."""
    
    def __init__(self, message: str, retry_after: int):
        """
        Initialize exception.
        
        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
        """
        super().__init__(message)
        self.retry_after = retry_after


class RedisRateLimiter(AbstractRateLimiter):
    """Redis-based sliding window rate limiter."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize rate limiter.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis = Redis.from_url(redis_url, decode_responses=False)
    
    async def check_limit(
        self,
        identifier: str,
        limit: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limit using sliding window.
        
        Args:
            identifier: User/IP identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if within limit
            
        Raises:
            RateLimitExceeded: If limit is exceeded
        """
        key = f"rate_limit:{identifier}"
        now = time.time()
        window_start = now - window_seconds
        
        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiry on the key
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        current_count = results[1]
        
        if current_count >= limit:
            # Calculate retry after
            retry_after = window_seconds
            raise RateLimitExceeded(
                f"Rate limit exceeded. Limit: {limit} requests per {window_seconds} seconds",
                retry_after=retry_after
            )
        
        return True
    
    async def get_remaining(self, identifier: str, limit: int = 10, window_seconds: int = 60) -> int:
        """
        Get remaining requests in current window.
        
        Args:
            identifier: User/IP identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Number of remaining requests
        """
        key = f"rate_limit:{identifier}"
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old entries and count
        await self.redis.zremrangebyscore(key, 0, window_start)
        current_count = await self.redis.zcard(key)
        
        remaining = max(0, limit - current_count)
        return remaining
    
    async def reset_limit(self, identifier: str) -> None:
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: User/IP identifier
        """
        key = f"rate_limit:{identifier}"
        await self.redis.delete(key)
    
    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


class InMemoryRateLimiter(AbstractRateLimiter):
    """In-memory rate limiter for testing/development."""
    
    def __init__(self):
        """Initialize in-memory rate limiter."""
        self.requests = {}  # identifier -> list of timestamps
    
    async def check_limit(
        self,
        identifier: str,
        limit: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """Check rate limit."""
        now = time.time()
        window_start = now - window_seconds
        
        # Get or create request list
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= limit:
            raise RateLimitExceeded(
                f"Rate limit exceeded. Limit: {limit} requests per {window_seconds} seconds",
                retry_after=window_seconds
            )
        
        # Add current request
        self.requests[identifier].append(now)
        
        return True
    
    async def get_remaining(self, identifier: str, limit: int = 10, window_seconds: int = 60) -> int:
        """Get remaining requests."""
        now = time.time()
        window_start = now - window_seconds
        
        if identifier not in self.requests:
            return limit
        
        # Count recent requests
        recent_requests = [
            ts for ts in self.requests[identifier]
            if ts > window_start
        ]
        
        remaining = max(0, limit - len(recent_requests))
        return remaining
    
    async def reset_limit(self, identifier: str) -> None:
        """Reset limit."""
        if identifier in self.requests:
            del self.requests[identifier]
