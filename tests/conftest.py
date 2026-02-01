"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_teaching_request():
    """Sample teaching request for tests."""
    from src.core.models import TeachingRequest, Subject, GradeLevel
    
    return TeachingRequest(
        student_id="test-student-123",
        question="What is photosynthesis?",
        subject=Subject.SCIENCE,
        grade_level=GradeLevel.MIDDLE_SCHOOL,
    )


@pytest.fixture
def sample_teaching_response():
    """Sample teaching response for tests."""
    from src.core.models import TeachingResponse
    
    return TeachingResponse(
        answer="Photosynthesis is the process by which plants...",
        model_used="phi3-mini-educational",
        tokens_used=150,
        estimated_cost=0.00015,
        confidence=0.88,
        processing_time_ms=1200,
        source="llm",
    )
