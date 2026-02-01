"""Structured logging configuration."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

from .config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.service_name,
            "version": settings.service_version,
            "environment": settings.environment,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add context fields
        for attr in ["request_id", "user_id", "model", "tokens_used", "cost"]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        return json.dumps(log_data)


def setup_logging():
    """
    Configure structured logging for the application.

    Sets up JSON formatting for production and readable format for development.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Set formatter based on environment
    if settings.log_format == "json" or settings.environment == "production":
        formatter = JSONFormatter()
    else:
        # Readable format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger
    """
    return logging.getLogger(name)


# Initialize logging on import
setup_logging()
