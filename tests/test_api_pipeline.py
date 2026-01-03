"""API tests for pipeline endpoints."""
import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.utils.errors import ErrorCode


class TestPipelineAPI:
    """Test /api/pipeline endpoint."""
    
    @pytest.mark.api
    def test_health_endpoint(self, client: TestClient):
        """Should return 200 for health check."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.api
    def test_pipeline_missing_file(self, client: TestClient):
        """Should return 422 when file is missing."""
        response = client.post("/api/pipeline")
        assert response.status_code == 422
    
    @pytest.mark.api
    def test_pipeline_invalid_file_type(self, client: TestClient):
        """Should reject invalid file types."""
        # Create a fake .txt file
        file_content = b"This is not an audio file"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post("/api/pipeline", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == ErrorCode.INVALID_FILE_FORMAT.value
    
    @pytest.mark.api
    def test_pipeline_file_too_large(self, client: TestClient, monkeypatch):
        """Should reject files exceeding size limit."""
        # Temporarily set very small limit
        from src.utils import settings
        monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 0.001)  # 1KB limit
        
        # Create a 2KB file
        large_content = b"0" * 2048
        files = {"file": ("large.mp3", io.BytesIO(large_content), "audio/mpeg")}
        
        response = client.post("/api/pipeline", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == ErrorCode.FILE_TOO_LARGE.value
    
    @pytest.mark.api
    def test_pipeline_invalid_ratio(self, client: TestClient, sample_audio_file):
        """Should reject invalid ratio parameters."""
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            # Ratio > 1.0
            response = client.post(
                "/api/pipeline",
                files=files,
                data={"ratio": 1.5}
            )
        
        assert response.status_code == 422
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_pipeline_success_async(
        self,
        client: TestClient,
        sample_audio_file,
        mock_full_pipeline
    ):
        """Should successfully process audio in async mode."""
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("lecture.mp3", f, "audio/mpeg")}
            data = {
                "ratio": 0.15,
                "subject": "cardiology",
                "async_mode": True
            }
            
            response = client.post("/api/pipeline", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert "task_id" in result
        assert result["status"] == "processing"
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_pipeline_phi_rejection(
        self,
        client: TestClient,
        sample_audio_file,
        sample_transcript_with_phi
    ):
        """Should reject audio containing PHI."""
        # Mock transcriber to return PHI-containing text
        with patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe:
            mock_transcribe.return_value = {
                "text": sample_transcript_with_phi,
                "segments": [],
                "language": "en",
                "duration": 30.0
            }
            
            with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess:
                mock_preprocess.return_value = (
                    "/tmp/test.wav",
                    {"enhanced": False, "enhancer": None}
                )
                
                with open(sample_audio_file, "rb") as f:
                    files = {"file": ("clinical_recording.mp3", f, "audio/mpeg")}
                    data = {"async_mode": False}  # Use sync for immediate result
                    
                    response = client.post("/api/pipeline", files=files, data=data)
        
        # Should return 400 with PHI error
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == ErrorCode.PHI_DETECTED.value
        assert "educational use only" in data["detail"]["message"].lower()
    
    @pytest.mark.api
    def test_get_task_status_not_found(self, client: TestClient):
        """Should return 404 for non-existent task."""
        response = client.get("/api/pipeline/nonexistent-task-id")
        assert response.status_code == 404
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_get_task_status_success(
        self,
        client: TestClient,
        sample_audio_file,
        mock_full_pipeline
    ):
        """Should return task status after submission."""
        # Submit task
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("lecture.mp3", f, "audio/mpeg")}
            response = client.post(
                "/api/pipeline",
                files=files,
                data={"async_mode": True}
            )
        
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # Check status
        status_response = client.get(f"/api/pipeline/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["task_id"] == task_id
        assert "status" in status_data
        assert "progress" in status_data
    
    @pytest.mark.api
    def test_cancel_task(self, client: TestClient, sample_audio_file, mock_full_pipeline):
        """Should be able to cancel pending task."""
        # Submit task
        with open(sample_audio_file, "rb") as f:
            files = {"file": ("lecture.mp3", f, "audio/mpeg")}
            response = client.post(
                "/api/pipeline",
                files=files,
                data={"async_mode": True}
            )
        
        task_id = response.json()["task_id"]
        
        # Cancel task
        cancel_response = client.delete(f"/api/pipeline/{task_id}")
        
        # Note: Might fail if task already completed
        # This is expected behavior
        assert cancel_response.status_code in [200, 400]


class TestPipelineValidation:
    """Test validation logic for pipeline inputs."""
    
    @pytest.mark.unit
    def test_sanitize_subject(self):
        """Should sanitize subject input."""
        from src.utils.validation import sanitize_subject
        
        # Normal case
        assert sanitize_subject("Cardiology") == "Cardiology"
        
        # SQL injection attempt
        dangerous = "test'; DROP TABLE users; --"
        sanitized = sanitize_subject(dangerous)
        assert "DROP" not in sanitized or len(sanitized) < len(dangerous)
        
        # None case
        assert sanitize_subject(None) is None
    
    @pytest.mark.unit
    def test_validate_ratio(self):
        """Should validate ratio parameter."""
        from src.utils.validation import validate_ratio
        
        # Valid ratios
        assert validate_ratio(0.15) == 0.15
        assert validate_ratio(0.5) == 0.5
        assert validate_ratio(1.0) == 1.0
        
        # Invalid ratios should raise
        with pytest.raises(Exception):
            validate_ratio(0.01)  # Too small
        
        with pytest.raises(Exception):
            validate_ratio(1.5)  # Too large
    
    @pytest.mark.unit
    def test_validate_file_extension(self):
        """Should validate file extensions."""
        from src.utils.validation import validate_file_extension
        
        # Valid extensions
        assert validate_file_extension("lecture.mp3") == ".mp3"
        assert validate_file_extension("audio.wav") == ".wav"
        
        # Invalid extensions should raise
        with pytest.raises(Exception):
            validate_file_extension("document.pdf")
        
        with pytest.raises(Exception):
            validate_file_extension("script.py")


class TestPipelineErrorHandling:
    """Test error handling in pipeline."""
    
    @pytest.mark.integration
    def test_whisper_failure(self, client: TestClient, sample_audio_file):
        """Should handle Whisper transcription failures."""
        with patch("src.api.services.transcriber.transcribe_audio") as mock:
            mock.side_effect = Exception("Whisper model failed")
            
            with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess:
                mock_preprocess.return_value = (
                    "/tmp/test.wav",
                    {"enhanced": False, "enhancer": None}
                )
                
                with open(sample_audio_file, "rb") as f:
                    files = {"file": ("test.mp3", f, "audio/mpeg")}
                    response = client.post(
                        "/api/pipeline",
                        files=files,
                        data={"async_mode": False}
                    )
        
        # Should return error
        assert response.status_code in [500, 400]
    
    @pytest.mark.integration
    def test_ollama_failure(self, client: TestClient, sample_audio_file):
        """Should handle Ollama summarization failures."""
        with patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe:
            mock_transcribe.return_value = {
                "text": "Test transcript",
                "segments": [],
                "language": "en",
                "duration": 10.0
            }
            
            with patch("src.api.services.summarizer.generate_summary") as mock_summarize:
                mock_summarize.side_effect = Exception("Ollama unavailable")
                
                with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess:
                    mock_preprocess.return_value = (
                        "/tmp/test.wav",
                        {"enhanced": False, "enhancer": None}
                    )
                    
                    with open(sample_audio_file, "rb") as f:
                        files = {"file": ("test.mp3", f, "audio/mpeg")}
                        response = client.post(
                            "/api/pipeline",
                            files=files,
                            data={"async_mode": False}
                        )
        
        # Should return error
        assert response.status_code in [500, 503]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
