"""Ollama LLM provider implementation."""

import time
import httpx
from typing import Dict, Any, AsyncGenerator, Optional
from .base import (
    BaseLLMProvider,
    ProviderError,
    ProviderUnavailableError,
    ProviderTimeoutError,
)
from ...core.models import LLMResponse, ModelHealth


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider implementation for local/self-hosted models."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama provider.

        Args:
            config: Provider configuration with base_url, timeout, etc.
        """
        super().__init__("ollama", config)
        self.client = httpx.AsyncClient(
            base_url=self.base_url, timeout=httpx.Timeout(self.timeout)
        )

    async def generate(
        self, prompt: str, model_config: Dict[str, Any], **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Ollama API.

        Args:
            prompt: Input prompt
            model_config: Model configuration
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with generated content

        Raises:
            ProviderError: If generation fails
        """
        start_time = time.time()

        model_name = model_config.get("model_name", "phi3:mini")
        system_prompt = model_config.get("system_prompt", "")
        temperature = kwargs.get("temperature", model_config.get("temperature", 0.7))
        max_tokens = kwargs.get("max_tokens", model_config.get("max_tokens", 1024))

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Ollama API request
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract response
            content = data.get("message", {}).get("content", "")

            # Extract token counts (if available)
            prompt_tokens = data.get(
                "prompt_eval_count", await self.count_tokens(prompt, model_config)
            )
            completion_tokens = data.get(
                "eval_count", await self.count_tokens(content, model_config)
            )

            return self._create_response(
                content=content,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                processing_time_ms=processing_time_ms,
                model_config=model_config,
                metadata={
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "eval_duration": data.get("eval_duration"),
                },
            )

        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(f"Ollama request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ollama HTTP error: {e}")
        except Exception as e:
            raise ProviderError(f"Ollama generation failed: {e}")

    async def stream_generate(
        self, prompt: str, model_config: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream response tokens from Ollama.

        Args:
            prompt: Input prompt
            model_config: Model configuration
            **kwargs: Additional parameters

        Yields:
            Response tokens as they're generated
        """
        model_name = model_config.get("model_name", "phi3:mini")
        system_prompt = model_config.get("system_prompt", "")
        temperature = kwargs.get("temperature", model_config.get("temperature", 0.7))
        max_tokens = kwargs.get("max_tokens", model_config.get("max_tokens", 1024))

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with self.client.stream(
                "POST", "/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json

                        data = json.loads(line)
                        if "message" in data:
                            content = data["message"].get("content", "")
                            if content:
                                yield content

                        # Check if done
                        if data.get("done", False):
                            break

        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(f"Ollama streaming timed out: {e}")
        except Exception as e:
            raise ProviderError(f"Ollama streaming failed: {e}")

    async def health_check(self) -> ModelHealth:
        """
        Check Ollama service health.

        Returns:
            ModelHealth with status
        """
        start_time = time.time()

        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()

            response_time_ms = int((time.time() - start_time) * 1000)

            return ModelHealth(
                model_id="ollama",
                provider=self.provider_name,
                status="healthy",
                response_time_ms=response_time_ms,
                error_rate=0.0,
                message="Ollama service is responsive",
            )

        except Exception as e:
            return ModelHealth(
                model_id="ollama",
                provider=self.provider_name,
                status="unavailable",
                error_rate=1.0,
                message=f"Health check failed: {str(e)}",
            )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
