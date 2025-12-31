"""Tests for pipeline endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestPipelineValidation:
    """Test pipeline validation."""

    def test_pipeline_missing_file(self, client):
        """Test pipeline with missing file."""
        response = client.post("/api/pipeline")
        assert response.status_code == 422

    def test_pipeline_invalid_ratio(self, client, sample_audio_bytes):
        """Test pipeline with invalid ratio."""
        response = client.post(
            "/api/pipeline",
            files={"file": ("test.wav", sample_audio_bytes)},
            params={"ratio": 1.5}
        )
        assert response.status_code == 422

    def test_pipeline_ratio_too_low(self, client, sample_audio_bytes):
        """Test pipeline with ratio below minimum."""
        response = client.post(
            "/api/pipeline",
            files={"file": ("test.wav", sample_audio_bytes)},
            params={"ratio": 0.01}
        )
        assert response.status_code == 422

    def test_pipeline_valid_ratio_range(self, client, sample_audio_bytes):
        """Test pipeline with valid ratio values."""
        for ratio in [0.05, 0.15, 0.50, 1.0]:
            response = client.post(
                "/api/pipeline",
                files={"file": ("test.wav", sample_audio_bytes)},
                params={"ratio": ratio, "async_mode": True}
            )
            assert response.status_code in [200, 500]


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "version" in data
        assert "timestamp" in data
