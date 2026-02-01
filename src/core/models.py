"""Domain models using Pydantic for validation and serialization."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class GradeLevel(str, Enum):
    """Student grade levels."""

    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"


class Subject(str, Enum):
    """Academic subjects."""

    MATH = "math"
    SCIENCE = "science"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    LITERATURE = "literature"
    ENGLISH = "english"
    COMPUTER_SCIENCE = "computer_science"
    OTHER = "other"


class ConversationMessage(BaseModel):
    """A single message in a conversation."""

    model_config = ConfigDict(protected_namespaces=())

    role: str
    content: str
    timestamp: Optional[datetime] = None


class TeachingRequest(BaseModel):
    """Request for teaching assistance."""

    model_config = ConfigDict(protected_namespaces=())

    student_id: str
    question: str
    subject: Subject
    grade_level: GradeLevel
    conversation_history: Optional[List[ConversationMessage]] = Field(
        default_factory=list
    )
    model_preference: Optional[str] = None

    @field_validator("conversation_history", mode="before")
    @classmethod
    def validate_history(cls, v):
        """Limit conversation history size."""
        if v and len(v) > 20:
            return v[-20:]  # Keep last 20 messages
        return v


class LLMResponse(BaseModel):
    """Response from an LLM provider."""

    model_config = ConfigDict(protected_namespaces=())

    content: str
    model_used: str
    tokens_used: int
    processing_time_ms: int


class TeachingResponse(BaseModel):
    """Response for teaching assistance request."""

    model_config = ConfigDict(protected_namespaces=())

    answer: str
    model_used: str
    tokens_used: int
    estimated_cost: float
    confidence: float
    source: str
    processing_time_ms: int
    follow_up_suggestions: List[str] = Field(default_factory=list)


class UsageMetrics(BaseModel):
    """Token usage and cost metrics."""

    model_config = ConfigDict(protected_namespaces=())

    total_tokens: int
    total_cost: float
    request_count: int


class ModelHealth(BaseModel):
    """Health status of an LLM model."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    status: str
    latency_ms: Optional[int] = None
    last_checked: datetime


class CacheKey(BaseModel):
    """Cache key for teaching responses."""

    model_config = ConfigDict(protected_namespaces=())

    question: str
    subject: str
    grade_level: str
