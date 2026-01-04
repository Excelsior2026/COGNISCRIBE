"""Unit tests for health check endpoint."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.main import app


class TestHealthCheckEndpoint:
    """Test /api/health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_all_healthy(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when all services are healthy."""
        # Mock Whisper model loaded successfully
        mock_whisper.return_value = Mock()
        
        # Mock Ollama tags endpoint
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        
        # Mock Ollama generate endpoint
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["whisper"]["loaded"] is True
        assert data["ollama"]["available"] is True
        assert "error" not in data["whisper"]
        assert "error" not in data["ollama"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_whisper_failure(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when Whisper model fails to load."""
        # Mock Whisper failure
        mock_whisper.side_effect = RuntimeError("Model not found")
        
        # Mock Ollama healthy
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/api/health")
        
        assert response.status_code == 503  # Service degraded
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["whisper"]["loaded"] is False
        assert "error" in data["whisper"]
        assert "Model not found" in data["whisper"]["error"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    def test_health_check_ollama_connection_error(self, mock_get, mock_whisper, client):
        """Test health check when Ollama is unavailable."""
        # Mock Whisper healthy
        mock_whisper.return_value = Mock()
        
        # Mock Ollama connection error
        mock_get.side_effect = Exception("Connection refused")
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["whisper"]["loaded"] is True
        assert data["ollama"]["available"] is False
        assert "error" in data["ollama"]
        assert "Connection refused" in data["ollama"]["error"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_ollama_tags_failure(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when Ollama tags endpoint fails."""
        # Mock Whisper healthy
        mock_whisper.return_value = Mock()
        
        # Mock Ollama tags failure
        mock_tags_response = Mock()
        mock_tags_response.status_code = 500
        mock_get.return_value = mock_tags_response
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "degraded"
        assert "Tags check returned 500" in data["ollama"]["error"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_ollama_generate_failure(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when Ollama generate endpoint fails."""
        # Mock Whisper healthy
        mock_whisper.return_value = Mock()
        
        # Mock Ollama tags success
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        
        # Mock Ollama generate failure
        mock_generate_response = Mock()
        mock_generate_response.status_code = 404
        mock_generate_response.text = "Model not found"
        mock_post.return_value = mock_generate_response
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["ollama"]["available"] is False
        assert "Generate check returned 404" in data["ollama"]["error"]
        assert "Model not found" in data["ollama"]["error"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    def test_health_check_both_services_down(self, mock_get, mock_whisper, client):
        """Test health check when both services are down."""
        # Mock both failures
        mock_whisper.side_effect = RuntimeError("Whisper failed")
        mock_get.side_effect = Exception("Ollama unavailable")
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["whisper"]["loaded"] is False
        assert data["ollama"]["available"] is False
        assert "error" in data["whisper"]
        assert "error" in data["ollama"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_response_structure(self, mock_post, mock_get, mock_whisper, client):
        """Test health check response contains all expected fields."""
        # Mock everything healthy
        mock_whisper.return_value = Mock()
        mock_tags = Mock()
        mock_tags.status_code = 200
        mock_get.return_value = mock_tags
        mock_gen = Mock()
        mock_gen.status_code = 200
        mock_post.return_value = mock_gen
        
        response = client.get("/api/health")
        data = response.json()
        
        # Verify structure
        assert "status" in data
        assert "whisper" in data
        assert "ollama" in data
        
        # Whisper details
        assert "model" in data["whisper"]
        assert "device" in data["whisper"]
        assert "loaded" in data["whisper"]
        
        # Ollama details
        assert "url" in data["ollama"]
        assert "available" in data["ollama"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_timeout_handling(self, mock_post, mock_get, mock_whisper, client):
        """Test health check handles timeouts gracefully."""
        # Mock Whisper healthy
        mock_whisper.return_value = Mock()
        
        # Mock timeout on Ollama
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "degraded"
        assert "timed out" in data["ollama"]["error"].lower()
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_ollama_validation(self, mock_post, mock_get, mock_whisper, client):
        """Test health check validates Ollama can actually generate."""
        # Mock Whisper healthy
        mock_whisper.return_value = Mock()
        
        # Mock tags success
        mock_tags = Mock()
        mock_tags.status_code = 200
        mock_get.return_value = mock_tags
        
        # Mock generate success
        mock_gen = Mock()
        mock_gen.status_code = 200
        mock_post.return_value = mock_gen
        
        response = client.get("/api/health")
        
        # Verify generate was actually called
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        
        # Verify minimal generation request
        assert "json" in call_kwargs
        assert call_kwargs["json"]["prompt"] == "healthcheck"
        assert call_kwargs["json"]["stream"] is False
        assert call_kwargs["json"]["options"]["num_predict"] == 1


class TestHealthCheckSettings:
    """Test health check reports correct settings."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_whisper_settings(self, mock_post, mock_get, mock_whisper, client):
        """Test health check reports Whisper settings."""
        mock_whisper.return_value = Mock()
        mock_get.return_value = Mock(status_code=200)
        mock_post.return_value = Mock(status_code=200)
        
        response = client.get("/api/health")
        data = response.json()
        
        # Should report model and device
        assert data["whisper"]["model"] is not None
        assert data["whisper"]["device"] is not None
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_ollama_settings(self, mock_post, mock_get, mock_whisper, client):
        """Test health check reports Ollama settings."""
        mock_whisper.return_value = Mock()
        mock_get.return_value = Mock(status_code=200)
        mock_post.return_value = Mock(status_code=200)
        
        response = client.get("/api/health")
        data = response.json()
        
        # Should report Ollama URL
        assert data["ollama"]["url"] is not None
        assert data["ollama"]["url"].startswith("http")
