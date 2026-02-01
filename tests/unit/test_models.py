"""Unit tests for core models."""

import pytest
from datetime import datetime
from src.core.models import (
    TeachingRequest,
    TeachingResponse,
    LLMResponse,
    UsageMetrics,
    Subject,
    GradeLevel,
    ConversationMessage,
)


def test_teaching_request_validation():
    """Test teaching request validation."""
    request = TeachingRequest(
        student_id="test-123",
        question="What is Python?",
        subject=Subject.COMPUTER_SCIENCE,
        grade_level=GradeLevel.HIGH_SCHOOL,
    )

    assert request.student_id == "test-123"
    assert request.question == "What is Python?"
    assert request.subject == Subject.COMPUTER_SCIENCE
    assert request.grade_level == GradeLevel.HIGH_SCHOOL


def test_teaching_request_with_history():
    """Test teaching request with conversation history."""
    history = [
        ConversationMessage(role="user", content="Hello"),
        ConversationMessage(role="assistant", content="Hi! How can I help?"),
    ]

    request = TeachingRequest(
        student_id="test-123",
        question="Follow up question",
        subject=Subject.MATH,
        grade_level=GradeLevel.MIDDLE_SCHOOL,
        conversation_history=history,
    )

    assert len(request.conversation_history) == 2


def test_teaching_request_history_limit():
    """Test that conversation history is limited to 20 messages."""
    # Create 25 messages
    history = [
        ConversationMessage(role="user", content=f"Message {i}") for i in range(25)
    ]

    request = TeachingRequest(
        student_id="test-123",
        question="Question",
        subject=Subject.MATH,
        grade_level=GradeLevel.ELEMENTARY,
        conversation_history=history,
    )

    # Should be limited to 20
    assert len(request.conversation_history) == 20


def test_llm_response_model():
    """Test LLM response model."""
    response = LLMResponse(
        content="This is a response",
        model="phi3:mini",
        tokens_used=100,
        prompt_tokens=50,
        completion_tokens=50,
        processing_time_ms=500,
        cost=0.0001,
        provider="ollama",
    )

    assert response.tokens_used == 100
    assert response.cost == 0.0001


def test_teaching_response_model():
    """Test teaching response model."""
    response = TeachingResponse(
        answer="Here's the explanation...",
        model_used="phi3-mini",
        tokens_used=150,
        estimated_cost=0.00015,
        confidence=0.85,
        processing_time_ms=1200,
    )

    assert response.confidence >= 0.0
    assert response.confidence <= 1.0
    assert response.source == "llm"  # Default value


def test_usage_metrics():
    """Test usage metrics model."""
    metrics = UsageMetrics(
        user_id="user-123",
        model="phi3-mini",
        tokens_used=200,
        cost=0.0002,
    )

    assert metrics.tokens_used == 200
    assert isinstance(metrics.timestamp, datetime)


def test_cache_key_generation():
    """Test cache key generation."""
    from src.core.models import CacheKey

    cache_key = CacheKey(
        question_hash="abc123",
        subject="math",
        grade_level="middle_school",
        model_id="phi3-mini",
    )

    key_string = cache_key.to_key()
    assert "teaching" in key_string
    assert "math" in key_string
    assert "middle_school" in key_string
