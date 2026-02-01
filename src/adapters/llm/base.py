"""Base LLM provider implementation with common utilities."""

import time
import hashlib
from typing import Dict, Any, Optional
from abc import ABC
from ...core.ports import AbstractLLMProvider
from ...core.models import LLMResponse, ModelHealth


class BaseLLMProvider(AbstractLLMProvider, ABC):
    """Base class with common LLM provider functionality."""

    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """
        Initialize base provider.

        Args:
            provider_name: Name of the provider (e.g., "ollama", "openai")
            config: Provider-specific configuration
        """
        self.provider_name = provider_name
        self.config = config
        self.base_url = config.get("base_url", "")
        self.timeout = config.get("timeout", 30)
        self.health_check_path = config.get("health_check_path", "/")

    def calculate_cost(self, tokens: int, model_config: Dict[str, Any]) -> float:
        """
        Calculate cost based on token usage.

        Args:
            tokens: Number of tokens used
            model_config: Model configuration with cost_per_1k_tokens

        Returns:
            Cost in USD
        """
        cost_per_1k = model_config.get("cost_per_1k_tokens", 0.0)
        return (tokens / 1000.0) * cost_per_1k

    async def count_tokens(self, text: str, model_config: Dict[str, Any]) -> int:
        """
        Estimate token count (rough approximation).

        More accurate implementations should use tiktoken or model-specific tokenizers.

        Args:
            text: Text to count tokens for
            model_config: Model configuration

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        # Override this in specific providers for better accuracy
        return len(text) // 4

    def _create_response(
        self,
        content: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        processing_time_ms: int,
        model_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Create a standardized LLMResponse.

        Args:
            content: Generated text
            model_name: Model identifier
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            processing_time_ms: Processing time
            model_config: Model configuration
            metadata: Additional metadata

        Returns:
            LLMResponse
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(total_tokens, model_config)

        return LLMResponse(
            content=content,
            model=model_name,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            processing_time_ms=processing_time_ms,
            cost=cost,
            provider=self.provider_name,
            metadata=metadata or {},
        )

    def _hash_prompt(self, prompt: str) -> str:
        """
        Create a hash of the prompt for caching/deduplication.

        Args:
            prompt: Prompt text

        Returns:
            SHA256 hash
        """
        return hashlib.sha256(prompt.encode()).hexdigest()


class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class ProviderUnavailableError(ProviderError):
    """Provider is unavailable or unhealthy."""

    pass


class ProviderTimeoutError(ProviderError):
    """Provider request timed out."""

    pass


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""

    pass
