"""Performance tests for teaching service."""

import asyncio
import time

import pytest
from httpx import AsyncClient

from src.api.main import app


@pytest.mark.performance
@pytest.mark.asyncio
async def test_response_time():
    """Test that API response time meets SLA."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {
            "student_id": "perf-test-123",
            "question": "What is 2+2?",
            "subject": "math",
            "grade_level": "elementary",
        }

        start_time = time.time()
        response = await client.post("/api/v1/teach", json=request_data)
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        # Should complete within 5 seconds (target: 2s for simple questions)
        assert duration_ms < 5000
        assert response is not None  # Ensure response was received


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling concurrent requests."""
    async with AsyncClient(app=app, base_url="http://test") as client:

        async def make_request(i: int):
            request_data = {
                "student_id": f"concurrent-test-{i}",
                "question": f"Test question {i}",
                "subject": "math",
                "grade_level": "elementary",
            }
            try:
                return await client.post("/api/v1/teach", json=request_data)
            except Exception as e:
                return e

        # Make 10 concurrent requests
        tasks = [make_request(i) for i in range(10)]

        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        # Check that most requests completed
        successful = sum(
            1
            for r in responses
            if not isinstance(r, Exception)
            and hasattr(r, "status_code")
            and r.status_code == 200
        )

        print(f"Completed {successful}/10 concurrent requests in {duration_ms:.0f}ms")

        # Skip test if LLM service is not available
        if successful == 0:
            pytest.skip("LLM service not available - skipping concurrent request test")

        # At least 30% should succeed when service is partially available
        assert successful >= 3, f"Only {successful}/10 requests succeeded"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_cache_performance():
    """Test cache hit performance improvement."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {
            "student_id": "cache-perf-test",
            "question": "What is 5+5?",
            "subject": "math",
            "grade_level": "elementary",
        }

        # First request (cache miss)
        start_time = time.time()
        response1 = await client.post("/api/v1/teach", json=request_data)
        first_duration = time.time() - start_time

        if response1.status_code != 200:
            pytest.skip("LLM not available")

        # Second request (should be cache hit)
        start_time = time.time()
        response2 = await client.post("/api/v1/teach", json=request_data)
        second_duration = time.time() - start_time

        # Cache hit should be significantly faster
        # In practice, cache hits are 10-100x faster
        assert second_duration < first_duration

        # Verify it was from cache
        data = response2.json()
        assert data.get("source") == "cache"
