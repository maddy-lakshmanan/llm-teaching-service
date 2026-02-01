"""Redis cache implementation."""

import json
import hashlib
from typing import Optional, Dict, Any
from redis.asyncio import Redis
from ...core.ports import AbstractCacheService
from ...core.models import (
    TeachingRequest,
    TeachingResponse,
    Subject,
    GradeLevel,
)


class RedisCacheService(AbstractCacheService):
    """Redis-based caching service for teaching responses."""

    def __init__(
        self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600
    ):
        """
        Initialize Redis cache service.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = default_ttl
        self._hit_count = 0
        self._miss_count = 0

    def _generate_cache_key(self, request: TeachingRequest) -> str:
        """
        Generate cache key from teaching request.

        Args:
            request: Teaching request

        Returns:
            Cache key string
        """
        # Create cache key components
        question_hash = hashlib.sha256(request.question.encode()).hexdigest()[:16]
        subject = request.subject.value
        grade_level = request.grade_level.value
        model = request.model_preference or "default"

        # Generate key string manually
        return f"teaching:{subject}:{grade_level}:{model}:{question_hash}"

    async def get_teaching_response(
        self, request: TeachingRequest
    ) -> Optional[TeachingResponse]:
        """
        Get cached teaching response.

        Args:
            request: Teaching request

        Returns:
            Cached response if exists, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(request)
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                self._hit_count += 1
                response_dict = json.loads(cached_data)
                return TeachingResponse(**response_dict)

            self._miss_count += 1
            return None

        except Exception as e:
            # Log error but don't fail - cache miss is acceptable
            print(f"Cache get error: {e}")
            self._miss_count += 1
            return None

    async def set_teaching_response(
        self,
        request: TeachingRequest,
        response: TeachingResponse,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Cache a teaching response.

        Args:
            request: Original teaching request
            response: Response to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
        """
        try:
            cache_key = self._generate_cache_key(request)
            ttl = ttl_seconds or self.default_ttl

            # Serialize response
            response_dict = response.model_dump()
            cached_data = json.dumps(response_dict, default=str)

            # Set with TTL
            await self.redis.setex(cache_key, ttl, cached_data)

        except Exception as e:
            # Log error but don't fail - cache write failure is acceptable
            print(f"Cache set error: {e}")

    async def invalidate_cache(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "teaching:math:*")

        Returns:
            Number of keys deleted
        """
        try:
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += await self.redis.delete(*keys)

                if cursor == 0:
                    break

            return deleted

        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dict with hit rate, miss rate, size, etc.
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0.0

        try:
            # Get Redis info
            info = await self.redis.info("stats")
            memory_info = await self.redis.info("memory")

            return {
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                "redis_keys": await self.redis.dbsize(),
                "memory_used_bytes": memory_info.get("used_memory", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "total_requests": total_requests,
            }

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


class InMemoryCacheService(AbstractCacheService):
    """In-memory cache for testing/development."""

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize in-memory cache.

        Args:
            default_ttl: Default TTL in seconds (not enforced in memory)
        """
        self._cache: Dict[str, TeachingResponse] = {}
        self.default_ttl = default_ttl
        self._hit_count = 0
        self._miss_count = 0

    def _generate_cache_key(self, request: TeachingRequest) -> str:
        """Generate cache key."""
        question_hash = hashlib.sha256(request.question.encode()).hexdigest()[:16]
        subject = request.subject.value
        grade_level = request.grade_level.value
        model = request.model_preference or "default"
        return f"teaching:{subject}:{grade_level}:{model}:{question_hash}"

    async def get_teaching_response(
        self, request: TeachingRequest
    ) -> Optional[TeachingResponse]:
        """Get cached response."""
        cache_key = self._generate_cache_key(request)

        if cache_key in self._cache:
            self._hit_count += 1
            return self._cache[cache_key]

        self._miss_count += 1
        return None

    async def set_teaching_response(
        self,
        request: TeachingRequest,
        response: TeachingResponse,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Cache a response."""
        cache_key = self._generate_cache_key(request)
        self._cache[cache_key] = response

    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries."""
        # Simple pattern matching for in-memory
        keys_to_delete = [
            k for k in self._cache.keys() if pattern.replace("*", "") in k
        ]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache stats."""
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0.0

        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "cache_size": len(self._cache),
        }
