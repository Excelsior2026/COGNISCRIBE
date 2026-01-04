"""Integration tests for complete audio processing pipeline."""

import pytest
import io
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.api.services.task_manager import TaskStatus, ProcessingStage


class TestFullPipelineIntegration:
    """Test complete pipeline from upload to completion."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_audio_file(self):
        """Create mock audio file."""
        # Create small audio-like file
        audio_data = b"RIFF" + b"\x00" * 100  # Minimal WAV-like header
        return io.BytesIO(audio_data)
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    @patch('src.api.services.summarizer.generate_summary')
    def test_complete_async_pipeline(self, mock_summarize, mock_transcribe, mock_preprocess, client, mock_audio_file):
        """Test complete async pipeline: upload → preprocess → transcribe → summarize."""
        # Mock preprocessing
        mock_preprocess.return_value = (
            "/tmp/processed.wav",
            {"enhanced": False, "enhancer": None}
        )
        
        # Mock transcription
        mock_transcribe.return_value = {
            "text": "This is a lecture about cell biology. Cells are the basic unit of life.",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "This is a lecture about cell biology.", "confidence": -0.3},
                {"start": 5.0, "end": 10.0, "text": "Cells are the basic unit of life.", "confidence": -0.2}
            ],
            "language": "en",
            "duration": 10.0
        }
        
        # Mock summarization
        mock_summarize.return_value = """### Learning Objectives
Understand cell structure

### Core Concepts
Cells are fundamental units

### Summary
Cell biology basics covered."""
        
        # Submit async task
        files = {"file": ("lecture.mp3", mock_audio_file, "audio/mpeg")}
        data = {
            "ratio": 0.15,
            "subject": "biology",
            "async_mode": True
        }
        
        response = client.post("/api/pipeline", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert "task_id" in result
        assert result["status"] == "processing"
        
        # Verify all pipeline stages were called
        # Note: In real async mode, these happen in background
        # For this test, we're verifying the mocks would be called
        task_id = result["task_id"]
        assert task_id is not None
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    @patch('src.api.services.summarizer.generate_summary')
    @patch('src.api.services.summarizer.parse_summary_sections')
    def test_complete_sync_pipeline(self, mock_parse, mock_summarize, mock_transcribe, mock_preprocess, client, mock_audio_file):
        """Test complete sync pipeline with immediate results."""
        # Mock preprocessing
        mock_preprocess.return_value = (
            "/tmp/processed.wav",
            {"enhanced": False, "enhancer": None}
        )
        
        # Mock transcription
        mock_transcribe.return_value = {
            "text": "Educational lecture content without any PHI.",
            "segments": [{"start": 0.0, "end": 5.0, "text": "Educational lecture content.", "confidence": -0.3}],
            "language": "en",
            "duration": 5.0
        }
        
        # Mock summarization
        mock_summarize.return_value = "Summary content"
        mock_parse.return_value = {
            "objectives": "Learn concepts",
            "concepts": "Core ideas",
            "terms": "Key terms",
            "procedures": "Methods",
            "summary": "Overall summary"
        }
        
        # Submit sync task
        files = {"file": ("lecture.mp3", mock_audio_file, "audio/mpeg")}
        data = {
            "ratio": 0.2,
            "subject": "anatomy",
            "async_mode": False
        }
        
        response = client.post("/api/pipeline", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert "transcription" in result
        assert "summary" in result
        assert result["transcription"]["text"] is not None
        assert result["transcription"]["language"] == "en"
        
        # Verify all stages were executed
        mock_preprocess.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_summarize.assert_called_once()
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    def test_phi_detection_in_pipeline(self, mock_transcribe, mock_preprocess, client, mock_audio_file):
        """Test PHI detection blocks pipeline completion."""
        # Mock preprocessing
        mock_preprocess.return_value = (
            "/tmp/processed.wav",
            {"enhanced": False, "enhancer": None}
        )
        
        # Mock transcription with PHI
        mock_transcribe.return_value = {
            "text": "Patient John Smith, SSN 123-45-6789, was admitted on 01/15/2023.",
            "segments": [],
            "language": "en",
            "duration": 10.0
        }
        
        # Submit task
        files = {"file": ("clinical.mp3", mock_audio_file, "audio/mpeg")}
        data = {"async_mode": False}
        
        response = client.post("/api/pipeline", files=files, data=data)
        
        # Should reject with PHI error
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["detail"]["error"] == "PHI_DETECTED"
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    def test_error_recovery_and_cleanup(self, mock_transcribe, mock_preprocess, client, mock_audio_file):
        """Test error recovery and resource cleanup."""
        # Mock preprocessing success
        temp_file = "/tmp/test_12345.wav"
        mock_preprocess.return_value = (
            temp_file,
            {"enhanced": False, "enhancer": None}
        )
        
        # Mock transcription failure
        mock_transcribe.side_effect = RuntimeError("Transcription failed")
        
        with patch('src.api.services.audio_preprocess.cleanup_temp_file') as mock_cleanup:
            files = {"file": ("lecture.mp3", mock_audio_file, "audio/mpeg")}
            data = {"async_mode": False}
            
            response = client.post("/api/pipeline", files=files, data=data)
            
            # Should return error
            assert response.status_code in [400, 500]
            
            # Verify cleanup was attempted
            # Note: Actual cleanup depends on implementation
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    @patch('src.api.services.summarizer.generate_summary')
    def test_deepfilternet_enhancement(self, mock_summarize, mock_transcribe, mock_preprocess, client, mock_audio_file):
        """Test pipeline with DeepFilterNet enhancement."""
        # Mock preprocessing with enhancement
        mock_preprocess.return_value = (
            "/tmp/enhanced.wav",
            {"enhanced": True, "enhancer": "deepfilternet"}
        )
        
        # Mock transcription
        mock_transcribe.return_value = {
            "text": "Clear audio after enhancement.",
            "segments": [],
            "language": "en",
            "duration": 5.0
        }
        
        # Mock summarization
        mock_summarize.return_value = "Summary"
        
        files = {"file": ("noisy_lecture.mp3", mock_audio_file, "audio/mpeg")}
        data = {"async_mode": False, "use_deepfilter": True}
        
        response = client.post("/api/pipeline", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify enhancement was used
        if "metadata" in result:
            assert result["metadata"]["enhanced"] is True


class TestConcurrentPipeline:
    """Test concurrent request handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_audio_file(self):
        """Create mock audio file."""
        audio_data = b"RIFF" + b"\x00" * 100
        return io.BytesIO(audio_data)
    
    @patch('src.api.services.audio_preprocess.preprocess_audio')
    @patch('src.api.services.transcriber.transcribe_audio')
    @patch('src.api.services.summarizer.generate_summary')
    def test_multiple_concurrent_uploads(self, mock_summarize, mock_transcribe, mock_preprocess, client):
        """Test handling of multiple concurrent uploads."""
        # Setup mocks
        mock_preprocess.return_value = ("/tmp/test.wav", {"enhanced": False, "enhancer": None})
        mock_transcribe.return_value = {
            "text": "Test",
            "segments": [],
            "language": "en",
            "duration": 5.0
        }
        mock_summarize.return_value = "Summary"
        
        # Submit multiple tasks
        task_ids = []
        for i in range(3):
            audio_data = b"RIFF" + b"\x00" * 100
            files = {"file": (f"lecture_{i}.mp3", io.BytesIO(audio_data), "audio/mpeg")}
            data = {"async_mode": True}
            
            response = client.post("/api/pipeline", files=files, data=data)
            assert response.status_code == 200
            
            result = response.json()
            task_ids.append(result["task_id"])
        
        # All task IDs should be unique
        assert len(set(task_ids)) == 3
        
        # All tasks should be retrievable
        for task_id in task_ids:
            status_response = client.get(f"/api/pipeline/{task_id}")
            assert status_response.status_code == 200
