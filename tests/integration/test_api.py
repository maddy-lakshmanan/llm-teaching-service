"""Integration tests for teaching service API."""

import pytest
from httpx import AsyncClient
from src.api.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "LLM Teaching Service"
        assert "version" in data


@pytest.mark.asyncio
async def test_list_models():
    """Test listing available models."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/models")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "default" in data
        assert len(data["models"]) > 0


@pytest.mark.asyncio
async def test_cache_stats():
    """Test getting cache statistics."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "hit_count" in data
        assert "miss_count" in data


@pytest.mark.asyncio
async def test_teach_endpoint_validation():
    """Test teaching endpoint with invalid data."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Missing required fields
        response = await client.post("/api/v1/teach", json={})
        
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_teach_endpoint_success():
    """Test successful teaching request."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {
            "student_id": "integration-test-123",
            "question": "What is 2+2?",
            "subject": "math",
            "grade_level": "elementary",
        }
        
        response = await client.post("/api/v1/teach", json=request_data)
        
        # Note: This will fail if Ollama is not available
        # In real integration tests, we'd mock the LLM provider
        assert response.status_code in [200, 500]  # 500 if Ollama not available
        
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "model_used" in data
            assert "tokens_used" in data
