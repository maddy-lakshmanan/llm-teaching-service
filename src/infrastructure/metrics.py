"""Monitoring and observability with OpenTelemetry."""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from contextlib import contextmanager

from ..core.ports import AbstractMonitoringService
from ..core.models import UsageMetrics

# OpenTelemetry imports (optional - only if installed)
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

# REMOVED: from ...core.ports import AbstractMonitoringService
# REMOVED: from .config import settings
# REMOVED: from .logging import get_logger

logger = logging.getLogger(__name__)


class MonitoringService(AbstractMonitoringService):
    """
    Centralized observability service with OpenTelemetry.
    
    Provides:
    - Distributed tracing
    - Metrics collection
    - Cost tracking
    - Performance monitoring
    """
    
    def __init__(self):
        """Initialize monitoring service."""
        # For now, disable monitoring features that need config/settings
        self.enabled = False  # Change this when you add proper config
        
        if not self.enabled:
            logger.warning("Monitoring is disabled or OpenTelemetry not available")
            return
        
        # Setup OpenTelemetry
        self._setup_tracing()
        self._setup_metrics()
        
        # Cost tracking
        self._total_cost = 0.0
        self._total_tokens = 0
        self._total_requests = 0
    
    def _setup_tracing(self):
        """Setup distributed tracing."""
        if not OTEL_AVAILABLE:
            return
        
        # Create resource
        resource = Resource.create({
            "service.name": "llm-teaching-service",
            "service.version": "1.0.0",
            "deployment.environment": "development",
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        self.tracer = trace.get_tracer(__name__)
    
    def _setup_metrics(self):
        """Setup metrics collection."""
        if not OTEL_AVAILABLE:
            return
        
        # Create resource
        resource = Resource.create({
            "service.name": "llm-teaching-service",
            "service.version": "1.0.0",
        })
        
        # Create meter provider
        meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(meter_provider)
        
        self.meter = metrics.get_meter(__name__)
        
        # Define metrics
        self.requests_counter = self.meter.create_counter(
            "llm_requests_total",
            description="Total LLM requests",
            unit="requests"
        )
        
        self.tokens_counter = self.meter.create_counter(
            "llm_tokens_total",
            description="Total tokens processed",
            unit="tokens"
        )
        
        self.cost_counter = self.meter.create_counter(
            "llm_cost_total",
            description="Total LLM cost in USD",
            unit="USD"
        )
        
        self.latency_histogram = self.meter.create_histogram(
            "llm_latency_ms",
            description="LLM request latency",
            unit="ms"
        )
        
        self.cache_hits_counter = self.meter.create_counter(
            "cache_hits_total",
            description="Total cache hits",
            unit="hits"
        )
        
        self.cache_misses_counter = self.meter.create_counter(
            "cache_misses_total",
            description="Total cache misses",
            unit="misses"
        )
    
    async def track_llm_call(
        self,
        model: str,
        tokens_used: int,
        cost: float,
        latency_ms: int,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Track LLM API call for monitoring."""
        if not self.enabled:
            return
        
        self._total_cost += cost
        self._total_tokens += tokens_used
        self._total_requests += 1
        
        attributes = {
            "model": model,
            "success": str(success).lower(),
        }
        
        if error:
            attributes["error_type"] = error
        
        try:
            self.requests_counter.add(1, attributes)
            self.tokens_counter.add(tokens_used, attributes)
            self.cost_counter.add(cost, attributes)
            self.latency_histogram.record(latency_ms, attributes)
            
            logger.info(f"LLM call tracked: {model}, tokens={tokens_used}, cost={cost}")
        except Exception as e:
            logger.error(f"Failed to track LLM call: {e}")
    
    async def record_cache_hit(self, cache_key: str) -> None:
        """Record cache hit for metrics."""
        if not self.enabled:
            return
        
        try:
            self.cache_hits_counter.add(1, {"cache_key_prefix": cache_key.split(":")[0]})
        except Exception as e:
            logger.error(f"Failed to record cache hit: {e}")
    
    async def record_cache_miss(self, cache_key: str) -> None:
        """Record cache miss for metrics."""
        if not self.enabled:
            return
        
        try:
            self.cache_misses_counter.add(1, {"cache_key_prefix": cache_key.split(":")[0]})
        except Exception as e:
            logger.error(f"Failed to record cache miss: {e}")
    
    @contextmanager
    def create_span(self, name: str):
        """Create a tracing span for distributed tracing."""
        if not self.enabled or not OTEL_AVAILABLE:
            yield None
            return
        
        with self.tracer.start_as_current_span(name) as span:
            yield span
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        return {
            "total_cost": self._total_cost,
            "total_tokens": self._total_tokens,
            "total_requests": self._total_requests,
            "average_cost_per_request": self._total_cost / self._total_requests if self._total_requests > 0 else 0,
            "average_tokens_per_request": self._total_tokens / self._total_requests if self._total_requests > 0 else 0,
        }


class NoOpMonitoringService(AbstractMonitoringService):
    """No-op monitoring service for development."""
    
    async def track_llm_call(
        self,
        model: str,
        tokens_used: int,
        cost: float,
        latency_ms: int,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """No-op implementation."""
        pass
    
    async def record_cache_hit(self, cache_key: str) -> None:
        """No-op implementation."""
        pass
    
    async def record_cache_miss(self, cache_key: str) -> None:
        """No-op implementation."""
        pass
    
    @contextmanager
    def create_span(self, name: str):
        """No-op implementation."""
        yield None