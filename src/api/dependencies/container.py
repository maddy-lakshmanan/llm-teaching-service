"""Dependency injection container."""

import os
from typing import Optional
from ...adapters.llm.factory import LLMProviderFactory, LLMConfiguration
from ...adapters.cache.redis_cache import RedisCacheService, InMemoryCacheService
from ...adapters.database.firestore_db import FirestoreService, InMemoryDatabaseService
from ...adapters.auth.firebase_auth import FirebaseAuthService, MockAuthService
from ...domain.rate_limit.rate_limiter import RedisRateLimiter, InMemoryRateLimiter
from ...domain.teaching.service import TeachingService
from ...infrastructure.metrics import MonitoringService


class Container:
    """
    Dependency injection container.
    
    Manages service lifecycles and dependency wiring.
    """
    
    def __init__(self):
        """Initialize container."""
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_production = self.environment == "production"
        
        # Services (initialized lazily)
        self._llm_factory: Optional[LLMProviderFactory] = None
        self._cache_service = None
        self._database_service = None
        self._rate_limiter = None
        self._auth_service = None
        self._monitoring_service = None
        self._teaching_service: Optional[TeachingService] = None
    
    async def initialize(self):
        """Initialize all services."""
        # Initialize services that need async setup
        pass
    
    async def cleanup(self):
        """Cleanup resources on shutdown."""
        # Close connections
        if self._cache_service and hasattr(self._cache_service, 'close'):
            await self._cache_service.close()
        
        if self._database_service and hasattr(self._database_service, 'close'):
            await self._database_service.close()
        
        if self._rate_limiter and hasattr(self._rate_limiter, 'close'):
            await self._rate_limiter.close()
        
        if self._llm_factory:
            await self._llm_factory.close_all()
    
    @property
    def llm_factory(self) -> LLMProviderFactory:
        """Get or create LLM factory."""
        if self._llm_factory is None:
            config = LLMConfiguration()
            self._llm_factory = LLMProviderFactory(config)
        return self._llm_factory
    
    @property
    def cache_service(self):
        """Get or create cache service."""
        if self._cache_service is None:
            if self.is_production:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self._cache_service = RedisCacheService(redis_url)
            else:
                # Use in-memory cache for development
                self._cache_service = InMemoryCacheService()
        return self._cache_service
    
    @property
    def database_service(self):
        """Get or create database service."""
        if self._database_service is None:
            if self.is_production:
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
                self._database_service = FirestoreService(project_id)
            else:
                # Use in-memory database for development
                self._database_service = InMemoryDatabaseService()
        return self._database_service
    
    @property
    def rate_limiter(self):
        """Get or create rate limiter."""
        if self._rate_limiter is None:
            if self.is_production:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self._rate_limiter = RedisRateLimiter(redis_url)
            else:
                # Use in-memory rate limiter for development
                self._rate_limiter = InMemoryRateLimiter()
        return self._rate_limiter
    
    @property
    def auth_service(self):
        """Get or create auth service."""
        if self._auth_service is None:
            if self.is_production:
                credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                self._auth_service = FirebaseAuthService(credentials_path)
            else:
                # Use mock auth for development
                self._auth_service = MockAuthService()
        return self._auth_service
    
    @property
    def monitoring_service(self):
        """Get or create monitoring service."""
        if self._monitoring_service is None:
            if self.is_production:
                self._monitoring_service = MonitoringService()
            # No monitoring in development
        return self._monitoring_service
    
    @property
    def teaching_service(self) -> TeachingService:
        """Get or create teaching service."""
        if self._teaching_service is None:
            self._teaching_service = TeachingService(
                llm_factory=self.llm_factory,
                cache_service=self.cache_service,
                database_service=self.database_service,
                rate_limiter=self.rate_limiter,
                monitoring_service=self.monitoring_service,
            )
        return self._teaching_service
