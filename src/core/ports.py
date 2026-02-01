"""Abstract interfaces (ports) for external dependencies."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any, List
from .models import (
    LLMResponse,
    TeachingRequest,
    TeachingResponse,
    UsageMetrics,
    ModelHealth,
    CacheKey
)


class AbstractLLMProvider(ABC):
    """Abstract interface for LLM providers (Ollama, OpenAI, Anthropic, etc.)."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: Input prompt
            model_config: Model-specific configuration
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with content, tokens, cost, etc.
        """
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream response tokens from the LLM.
        
        Args:
            prompt: Input prompt
            model_config: Model-specific configuration
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Response tokens as they're generated
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> ModelHealth:
        """
        Check if provider is healthy and responsive.
        
        Returns:
            ModelHealth with status and metrics
        """
        pass
    
    @abstractmethod
    def calculate_cost(self, tokens: int, model_config: Dict[str, Any]) -> float:
        """
        Calculate cost for token usage.
        
        Args:
            tokens: Number of tokens used
            model_config: Model configuration with pricing info
            
        Returns:
            Cost in USD
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model_config: Dict[str, Any]) -> int:
        """
        Count tokens in text for a specific model.
        
        Args:
            text: Text to tokenize
            model_config: Model configuration
            
        Returns:
            Token count
        """
        pass


class AbstractCacheService(ABC):
    """Abstract interface for caching service (Redis, Memcache, etc.)."""
    
    @abstractmethod
    async def get_teaching_response(
        self,
        request: TeachingRequest
    ) -> Optional[TeachingResponse]:
        """
        Get cached teaching response.
        
        Args:
            request: Teaching request
            
        Returns:
            Cached response if exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def set_teaching_response(
        self,
        request: TeachingRequest,
        response: TeachingResponse,
        ttl_seconds: int = 3600
    ) -> None:
        """
        Cache a teaching response.
        
        Args:
            request: Original teaching request
            response: Response to cache
            ttl_seconds: Time-to-live in seconds
        """
        pass
    
    @abstractmethod
    async def invalidate_cache(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "teaching:math:*")
            
        Returns:
            Number of keys deleted
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dict with hit rate, miss rate, size, etc.
        """
        pass


class AbstractDatabaseService(ABC):
    """Abstract interface for database operations (Firestore, PostgreSQL, etc.)."""
    
    @abstractmethod
    async def save_conversation(
        self,
        student_id: str,
        request: TeachingRequest,
        response: TeachingResponse
    ) -> str:
        """
        Save conversation to persistent storage.
        
        Args:
            student_id: Student identifier
            request: Teaching request
            response: Teaching response
            
        Returns:
            Conversation ID
        """
        pass
    
    @abstractmethod
    async def get_conversation_history(
        self,
        student_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve student's conversation history.
        
        Args:
            student_id: Student identifier
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of conversations
        """
        pass
    
    @abstractmethod
    async def save_usage_metrics(self, metrics: UsageMetrics) -> None:
        """
        Save token usage and cost metrics.
        
        Args:
            metrics: Usage metrics to save
        """
        pass
    
    @abstractmethod
    async def get_usage_summary(
        self,
        student_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary with aggregated metrics.
        
        Args:
            student_id: Filter by student (optional)
            start_date: Start date for range (optional)
            end_date: End date for range (optional)
            
        Returns:
            Usage summary with totals and breakdowns
        """
        pass


class AbstractRateLimiter(ABC):
    """Abstract interface for rate limiting."""
    
    @abstractmethod
    async def check_limit(
        self,
        identifier: str,
        limit: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: User/IP identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if within limit, False if exceeded
            
        Raises:
            RateLimitExceeded: If limit is exceeded
        """
        pass
    
    @abstractmethod
    async def get_remaining(self, identifier: str) -> int:
        """
        Get remaining requests in current window.
        
        Args:
            identifier: User/IP identifier
            
        Returns:
            Number of remaining requests
        """
        pass
    
    @abstractmethod
    async def reset_limit(self, identifier: str) -> None:
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: User/IP identifier
        """
        pass


class AbstractAuthService(ABC):
    """Abstract interface for authentication (Firebase Auth, etc.)."""
    
    @abstractmethod
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify authentication token.
        
        Args:
            token: Authentication token (JWT, Firebase token, etc.)
            
        Returns:
            User information if valid
            
        Raises:
            AuthenticationError: If token is invalid
        """
        pass
    
    @abstractmethod
    async def get_user_tier(self, user_id: str) -> str:
        """
        Get user's subscription tier.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tier name (e.g., 'free', 'premium', 'enterprise')
        """
        pass


class AbstractMonitoringService(ABC):
    """Abstract interface for monitoring and observability."""
    
    @abstractmethod
    async def track_llm_call(
        self,
        model: str,
        tokens_used: int,
        cost: float,
        latency_ms: int,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Track LLM API call for monitoring.
        
        Args:
            model: Model identifier
            tokens_used: Tokens consumed
            cost: Cost in USD
            latency_ms: Latency in milliseconds
            success: Whether call succeeded
            error: Error message if failed
        """
        pass
    
    @abstractmethod
    async def record_cache_hit(self, cache_key: str) -> None:
        """Record cache hit for metrics."""
        pass
    
    @abstractmethod
    async def record_cache_miss(self, cache_key: str) -> None:
        """Record cache miss for metrics."""
        pass
    
    @abstractmethod
    def create_span(self, name: str) -> Any:
        """
        Create a tracing span for distributed tracing.
        
        Args:
            name: Span name
            
        Returns:
            Span context manager
        """
        pass
