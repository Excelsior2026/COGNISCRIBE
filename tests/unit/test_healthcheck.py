"""Unit tests for health check endpoint."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.utils.errors import ProcessingError, ErrorCode


class TestHealthCheckEndpoint:
    """Test health check endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_all_healthy(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when all services are healthy."""
        # Mock Whisper model loaded
        mock_whisper.return_value = MagicMock()
        
        # Mock Ollama tags endpoint
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        
        # Mock Ollama generate endpoint
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["whisper"]["loaded"] is True
        assert data["ollama"]["available"] is True
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_whisper_info(self, mock_post, mock_get, mock_whisper, client):
        """Test health check includes Whisper configuration."""
        mock_whisper.return_value = MagicMock()
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/health")
        data = response.json()
        
        assert "whisper" in data
        assert "model" in data["whisper"]
        assert "device" in data["whisper"]
        assert "loaded" in data["whisper"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_ollama_info(self, mock_post, mock_get, mock_whisper, client):
        """Test health check includes Ollama configuration."""
        mock_whisper.return_value = MagicMock()
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/health")
        data = response.json()
        
        assert "ollama" in data
        assert "url" in data["ollama"]
        assert "available" in data["ollama"]


class TestHealthCheckWhisperFailures:
    """Test health check with Whisper failures."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_whisper_not_loaded(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when Whisper model fails to load."""
        # Mock Whisper model load failure
        mock_whisper.side_effect = ProcessingError(
            message="Model not found",
            error_code=ErrorCode.WHISPER_MODEL_LOAD_FAILED
        )
        
        # Mock Ollama healthy
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["whisper"]["loaded"] is False
        assert "error" in data["whisper"]
        assert "Model not found" in data["whisper"]["error"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_whisper_runtime_error(self, mock_post, mock_get, mock_whisper, client):
        """Test health check with Whisper runtime error."""
        mock_whisper.side_effect = RuntimeError("CUDA out of memory")
        
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert "CUDA out of memory" in data["whisper"]["error"]


class TestHealthCheckOllamaFailures:
    """Test health check with Ollama failures."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    def test_health_check_ollama_tags_failure(self, mock_get, mock_whisper, client):
        """Test health check when Ollama tags endpoint fails."""
        mock_whisper.return_value = MagicMock()
        
        # Mock Ollama tags failure
        mock_tags_response = Mock()
        mock_tags_response.status_code = 500
        mock_get.return_value = mock_tags_response
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama"]["available"] is False
        assert "error" in data["ollama"]
        assert "500" in data["ollama"]["error"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_ollama_generate_failure(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when Ollama generate endpoint fails."""
        mock_whisper.return_value = MagicMock()
        
        # Mock Ollama tags success
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        
        # Mock Ollama generate failure
        mock_generate_response = Mock()
        mock_generate_response.status_code = 404
        mock_generate_response.text = "model not found"
        mock_post.return_value = mock_generate_response
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama"]["available"] is False
        assert "404" in data["ollama"]["error"]
        assert "model not found" in data["ollama"]["error"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    def test_health_check_ollama_connection_error(self, mock_get, mock_whisper, client):
        """Test health check when Ollama is unreachable."""
        mock_whisper.return_value = MagicMock()
        
        # Mock Ollama connection error
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama"]["available"] is False
        assert "error" in data["ollama"]
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    def test_health_check_ollama_timeout(self, mock_get, mock_whisper, client):
        """Test health check when Ollama times out."""
        mock_whisper.return_value = MagicMock()
        
        # Mock Ollama timeout
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama"]["available"] is False


class TestHealthCheckDegradedStates:
    """Test various degraded states."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    @patch('src.api.routers.healthcheck.requests.post')
    def test_health_check_both_services_down(self, mock_post, mock_get, mock_whisper, client):
        """Test health check when both services are down."""
        # Both services fail
        mock_whisper.side_effect = RuntimeError("Model error")
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        response = client.get("/health")
        
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
    def test_health_check_returns_200_on_healthy(self, mock_post, mock_get, mock_whisper, client):
        """Test health check returns 200 when healthy."""
        mock_whisper.return_value = MagicMock()
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_get.return_value = mock_tags_response
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_post.return_value = mock_generate_response
        
        response = client.get("/health")
        
        assert response.status_code == 200
    
    @patch('src.api.routers.healthcheck.transcriber.get_model')
    @patch('src.api.routers.healthcheck.requests.get')
    def test_health_check_returns_503_on_degraded(self, mock_get, mock_whisper, client):
        """Test health check returns 503 when degraded."""
        mock_whisper.side_effect = RuntimeError("Error")
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Error")
        
        response = client.get("/health")
        
        assert response.status_code == 503
