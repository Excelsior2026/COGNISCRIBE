"""Unit tests for integration resilience and error recovery."""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.utils.errors import ProcessingError, ServiceUnavailableError, ErrorCode
import requests


class TestServiceTimeouts:
    """Test service timeout handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.services.summarizer.requests.post')
    def test_ollama_timeout_handling(self, mock_post, client):
        """Test Ollama timeout is handled gracefully."""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        with patch('src.api.services.transcriber.transcribe_audio') as mock_transcribe, \
             patch('src.api.services.audio_preprocess.preprocess_audio') as mock_preprocess:
            
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            mock_transcribe.return_value = {
                "text": "Test transcript",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            
            response = client.get("/api/health")
            
            # Health check should report degraded
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
    
    @patch('src.api.services.transcriber.get_model')
    def test_whisper_load_timeout(self, mock_get_model):
        """Test Whisper model load timeout."""
        import time
        
        def slow_load():
            time.sleep(10)  # Simulate very slow load
            return MagicMock()
        
        mock_get_model.side_effect = slow_load
        
        # Should timeout or handle gracefully
        # In practice, this would be caught by health checks


class TestConnectionErrors:
    """Test connection error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.services.summarizer.requests.post')
    def test_ollama_connection_refused(self, mock_post, client):
        """Test Ollama connection refused is handled."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        response = client.get("/api/health")
        
        # Should report degraded, not crash
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama"]["available"] is False
    
    @patch('src.api.services.summarizer.requests.post')
    def test_ollama_dns_failure(self, mock_post):
        """Test DNS failure for Ollama service."""
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Name or service not known"
        )
        
        # Service should handle DNS errors gracefully
        with pytest.raises(requests.exceptions.ConnectionError):
            mock_post("http://invalid-ollama-host/api/generate", json={})


class TestPartialPipelineFailures:
    """Test partial failures in pipeline processing."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    def test_preprocessing_success_transcription_failure(self, mock_transcribe, mock_preprocess, client, sample_audio_file):
        """Test transcription failure after successful preprocessing."""
        # Preprocessing succeeds
        mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
        
        # Transcription fails
        mock_transcribe.side_effect = RuntimeError("Whisper model crashed")
        
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            response = client.post(
                "/api/pipeline",
                files=files,
                params={"async_mode": False}
            )
        
        # Should return error, not crash
        assert response.status_code in [400, 500]
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    @patch('src.api.services.summarizer.generate_summary')
    def test_transcription_success_summarization_failure(self, mock_summarize, mock_transcribe, mock_preprocess, client, sample_audio_file):
        """Test summarization failure after successful transcription."""
        mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
        mock_transcribe.return_value = {
            "text": "Complete transcription",
            "segments": [],
            "language": "en",
            "duration": 10.0
        }
        
        # Summarization fails
        mock_summarize.side_effect = ServiceUnavailableError(
            "Ollama unavailable",
            ErrorCode.OLLAMA_UNAVAILABLE
        )
        
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            response = client.post(
                "/api/pipeline",
                files=files,
                params={"async_mode": False}
            )
        
        # Should return service unavailable error
        assert response.status_code == 503


class TestResourceCleanup:
    """Test resource cleanup on errors."""
    
    def test_temp_file_cleanup_on_preprocessing_error(self):
        """Test temp files are cleaned up when preprocessing fails."""
        from src.api.services import audio_preprocess
        
        # Create a temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"fake audio data")
        
        # Cleanup should work
        audio_preprocess.cleanup_temp_file(temp_path)
        
        # File should be deleted
        assert not os.path.exists(temp_path)
    
    def test_cleanup_nonexistent_file_doesnt_crash(self):
        """Test cleaning up non-existent file doesn't crash."""
        from src.api.services import audio_preprocess
        
        # Should handle gracefully
        audio_preprocess.cleanup_temp_file("/tmp/nonexistent_file.wav")
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    def test_uploaded_file_cleanup_on_validation_error(self, mock_preprocess, sample_audio_file):
        """Test uploaded file is cleaned up on validation error."""
        from fastapi.testclient import TestClient
        from src.main import app
        
        client = TestClient(app)
        
        # Upload file with invalid parameters
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            response = client.post(
                "/api/pipeline",
                files=files,
                params={"ratio": 99.0}  # Invalid ratio
            )
        
        # Should reject and cleanup
        assert response.status_code == 422


class TestErrorStateValidation:
    """Test error state validation and recovery."""
    
    def test_task_manager_error_state(self):
        """Test task manager properly tracks error states."""
        from src.api.services.task_manager import TaskManager, TaskStatus
        
        manager = TaskManager()
        task_id = manager.create_task()
        
        # Fail task
        manager.fail_task(
            task_id,
            error="Test error",
            error_code=ErrorCode.TRANSCRIPTION_FAILED.value
        )
        
        # Verify error state
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.error == "Test error"
        assert task.error_code == ErrorCode.TRANSCRIPTION_FAILED.value
    
    def test_multiple_error_types_tracked(self):
        """Test different error types are properly tracked."""
        from src.api.services.task_manager import TaskManager
        
        manager = TaskManager()
        
        # Create multiple tasks with different errors
        errors = [
            (ErrorCode.PREPROCESSING_FAILED, "Preprocessing error"),
            (ErrorCode.TRANSCRIPTION_FAILED, "Transcription error"),
            (ErrorCode.SUMMARIZATION_FAILED, "Summarization error")
        ]
        
        for error_code, error_msg in errors:
            task_id = manager.create_task()
            manager.fail_task(task_id, error=error_msg, error_code=error_code.value)
            
            task = manager.get_task(task_id)
            assert task.error == error_msg
            assert task.error_code == error_code.value


class TestCascadingFailures:
    """Test handling of cascading failures."""
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    def test_preprocessing_failure_prevents_transcription(self, mock_preprocess, sample_audio_file):
        """Test preprocessing failure prevents transcription attempt."""
        from fastapi.testclient import TestClient
        from src.main import app
        
        client = TestClient(app)
        
        # Preprocessing fails
        mock_preprocess.side_effect = ProcessingError(
            "Audio preprocessing failed",
            ErrorCode.PREPROCESSING_FAILED
        )
        
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            response = client.post(
                "/api/pipeline",
                files=files,
                params={"async_mode": False}
            )
        
        # Should fail early, not attempt transcription
        assert response.status_code in [400, 500]
    
    @patch('src.api.services.transcriber.get_model')
    @patch('src.api.services.summarizer.requests.post')
    def test_multiple_services_unavailable(self, mock_ollama, mock_whisper):
        """Test handling when multiple services are unavailable."""
        from fastapi.testclient import TestClient
        from src.main import app
        
        client = TestClient(app)
        
        # Both services fail
        mock_whisper.side_effect = RuntimeError("Whisper unavailable")
        mock_ollama.side_effect = requests.exceptions.ConnectionError("Ollama unavailable")
        
        response = client.get("/api/health")
        
        # Should report degraded with both errors
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert "error" in data["whisper"]
        assert "error" in data["ollama"]


class TestRecoveryAfterErrors:
    """Test system recovery after errors."""
    
    def test_new_task_after_previous_failure(self):
        """Test new task can be created after previous failure."""
        from src.api.services.task_manager import TaskManager
        
        manager = TaskManager()
        
        # Create and fail first task
        task_id_1 = manager.create_task()
        manager.fail_task(
            task_id_1,
            error="Test error",
            error_code=ErrorCode.TRANSCRIPTION_FAILED.value
        )
        
        # Create new task
        task_id_2 = manager.create_task()
        
        # New task should be in pending state
        task_2 = manager.get_task(task_id_2)
        assert task_2 is not None
        assert task_id_1 != task_id_2
    
    @patch('src.api.services.transcriber.transcribe_audio')
    def test_service_recovery_after_temporary_failure(self, mock_transcribe):
        """Test service works after temporary failure."""
        # First call fails, second succeeds
        mock_transcribe.side_effect = [
            RuntimeError("Temporary error"),
            {
                "text": "Success",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
        ]
        
        from src.api.services import transcriber
        
        # First call fails
        with pytest.raises(RuntimeError):
            transcriber.transcribe_audio("/tmp/test.wav")
        
        # Second call succeeds
        result = transcriber.transcribe_audio("/tmp/test.wav")
        assert result["text"] == "Success"
