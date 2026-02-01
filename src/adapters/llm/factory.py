"""LLM provider factory for creating and managing providers."""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from .base import BaseLLMProvider
from .ollama import OllamaProvider


class ModelConfig:
    """Model configuration wrapper."""

    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize model configuration.

        Args:
            config_dict: Configuration dictionary
        """
        self.name = config_dict.get("name", "")
        self.provider = config_dict.get("provider", "")
        self.model_name = config_dict.get("model_name", "")
        self.max_tokens = config_dict.get("max_tokens", 1024)
        self.temperature = config_dict.get("temperature", 0.7)
        self.system_prompt = config_dict.get("system_prompt", "")
        self.cost_per_1k_tokens = config_dict.get("cost_per_1k_tokens", 0.0)
        self._raw_config = config_dict

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._raw_config

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access."""
        return self._raw_config[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get with default."""
        return self._raw_config.get(key, default)


class LLMConfiguration:
    """Manages external LLM configurations from YAML."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to models.yaml (defaults to config/models.yaml)
        """
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent.parent / "config" / "models.yaml"
            )

        self.config_path = config_path
        self._config = self._load_config()
        self._models: Dict[str, ModelConfig] = {}
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._parse_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                # Substitute environment variables
                return self._substitute_env_vars(config)
        except FileNotFoundError:
            # Return default configuration if file doesn't exist
            return self._get_default_config()
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute ${VAR} with environment variables."""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif (
            isinstance(config, str) and config.startswith("${") and config.endswith("}")
        ):
            var_name = config[2:-1]
            return os.environ.get(var_name, config)
        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file doesn't exist."""
        return {
            "models": {
                "default": "phi3-mini-educational",
                "providers": {
                    "ollama-local": {
                        "type": "ollama",
                        "base_url": os.environ.get(
                            "OLLAMA_URL", "http://localhost:11434"
                        ),
                        "timeout": 30,
                        "health_check_path": "/api/tags",
                    }
                },
                "model_registry": {
                    "phi3-mini-educational": {
                        "provider": "ollama-local",
                        "model_name": "phi3:mini",
                        "max_tokens": 1024,
                        "temperature": 0.7,
                        "system_prompt": "You are an educational assistant for K-12 students.",
                        "cost_per_1k_tokens": 0.0001,
                    }
                },
            }
        }

    def _parse_config(self):
        """Parse configuration into internal structures."""
        models_section = self._config.get("models", {})

        # Parse providers
        self._providers = models_section.get("providers", {})

        # Parse model registry
        model_registry = models_section.get("model_registry", {})
        for model_id, model_config in model_registry.items():
            self._models[model_id] = ModelConfig({"name": model_id, **model_config})

        # Store default model
        self.default_model = models_section.get("default", "phi3-mini-educational")

    def get_model_config(self, model_id: Optional[str] = None) -> ModelConfig:
        """
        Get configuration for a specific model.

        Args:
            model_id: Model identifier (uses default if None)

        Returns:
            ModelConfig

        Raises:
            ValueError: If model_id not found
        """
        if model_id is None:
            model_id = self.default_model

        if model_id not in self._models:
            raise ValueError(f"Model '{model_id}' not found in configuration")

        return self._models[model_id]

    def get_provider_config(self, provider_id: str) -> Dict[str, Any]:
        """
        Get provider configuration.

        Args:
            provider_id: Provider identifier

        Returns:
            Provider configuration dict

        Raises:
            ValueError: If provider not found
        """
        if provider_id not in self._providers:
            raise ValueError(f"Provider '{provider_id}' not found in configuration")

        return self._providers[provider_id]

    def list_available_models(self) -> list[str]:
        """List all configured models."""
        return list(self._models.keys())

    def list_available_providers(self) -> list[str]:
        """List all configured providers."""
        return list(self._providers.keys())

    def hot_swap_model(self, model_id: str, new_config: Dict[str, Any]):
        """
        Dynamically update model configuration.

        Args:
            model_id: Model identifier
            new_config: New configuration
        """
        self._models[model_id] = ModelConfig({"name": model_id, **new_config})


class LLMProviderFactory:
    """Factory for creating and managing LLM providers."""

    def __init__(self, config: Optional[LLMConfiguration] = None):
        """
        Initialize provider factory.

        Args:
            config: LLM configuration (creates default if None)
        """
        self.config = config or LLMConfiguration()
        self._provider_instances: Dict[str, BaseLLMProvider] = {}

    def get_provider(self, provider_id: str) -> BaseLLMProvider:
        """
        Get or create a provider instance.

        Args:
            provider_id: Provider identifier

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider type is unsupported
        """
        # Return cached instance if exists
        if provider_id in self._provider_instances:
            return self._provider_instances[provider_id]

        # Get provider configuration
        provider_config = self.config.get_provider_config(provider_id)
        provider_type = provider_config.get("type", "")

        # Create provider based on type
        if provider_type == "ollama":
            provider = OllamaProvider(provider_config)
        # Add more provider types here (OpenAI, Anthropic, etc.)
        # elif provider_type == "openai":
        #     provider = OpenAIProvider(provider_config)
        # elif provider_type == "anthropic":
        #     provider = AnthropicProvider(provider_config)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        # Cache and return
        self._provider_instances[provider_id] = provider
        return provider

    def get_provider_for_model(self, model_id: Optional[str] = None) -> BaseLLMProvider:
        """
        Get provider for a specific model.

        Args:
            model_id: Model identifier (uses default if None)

        Returns:
            LLM provider instance
        """
        model_config = self.config.get_model_config(model_id)
        provider_id = model_config.provider
        return self.get_provider(provider_id)

    def get_model_config(self, model_id: Optional[str] = None) -> ModelConfig:
        """
        Get model configuration.

        Args:
            model_id: Model identifier (uses default if None)

        Returns:
            ModelConfig
        """
        return self.config.get_model_config(model_id)

    async def close_all(self):
        """Close all provider instances."""
        for provider in self._provider_instances.values():
            if hasattr(provider, "close"):
                await provider.close()
        self._provider_instances.clear()
