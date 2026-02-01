"""Unit tests for LLM provider factory."""

import pytest
from pathlib import Path
from src.adapters.llm.factory import (
    LLMConfiguration,
    LLMProviderFactory,
    ModelConfig,
)


def test_llm_configuration_default():
    """Test LLM configuration with default values."""
    # Use a non-existent path to trigger default config
    config = LLMConfiguration(Path("nonexistent.yaml"))
    
    assert config.default_model == "phi3-mini-educational"
    assert "phi3-mini-educational" in config.list_available_models()


def test_model_config_access():
    """Test accessing model configuration."""
    config = LLMConfiguration(Path("nonexistent.yaml"))
    
    model_config = config.get_model_config("phi3-mini-educational")
    
    assert model_config.provider == "ollama-local"
    assert model_config.model_name == "phi3:mini"
    assert model_config.max_tokens == 1024


def test_provider_factory_creation():
    """Test provider factory creation."""
    factory = LLMProviderFactory()
    
    assert factory.config is not None
    assert len(factory.config.list_available_models()) > 0


def test_get_provider_for_model():
    """Test getting provider for a model."""
    factory = LLMProviderFactory()
    
    provider = factory.get_provider_for_model("phi3-mini-educational")
    
    assert provider is not None
    assert provider.provider_name == "ollama"


@pytest.mark.asyncio
async def test_provider_factory_cleanup():
    """Test provider factory cleanup."""
    factory = LLMProviderFactory()
    
    # Get a provider to instantiate it
    provider = factory.get_provider_for_model()
    
    # Cleanup should not raise errors
    await factory.close_all()
