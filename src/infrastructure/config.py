"""Configuration management."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings from environment variables.

    All configuration is externalized via environment variables
    to support 12-factor app principles.
    """

    # Environment
    environment: str = "development"
    debug: bool = False

    # Service
    service_name: str = "llm-teaching-service"
    service_version: str = "1.0.0"

    # API
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 1

    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_timeout: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600

    # Google Cloud
    google_cloud_project: Optional[str] = None
    google_application_credentials: Optional[str] = None

    # Firebase
    firebase_credentials_path: Optional[str] = None

    # Rate Limiting
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60

    # Model Configuration
    model_config_path: str = "config/models.yaml"
    default_model: str = "phi3-mini-educational"

    # Monitoring
    enable_monitoring: bool = True
    enable_tracing: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # CORS
    cors_origins: list[str] = ["*"]

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
