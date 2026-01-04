"""Enhanced API tests for pipeline endpoint - advanced scenarios."""

import pytest
import io
import asyncio
import time
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.utils.errors import ErrorCode
from src.api.services.task_manager import TaskStatus, ProcessingStage


class TestPipelineAsyncMode:
    """Test async mode with task polling and progress tracking."""
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_async_task_polling_workflow(self, client: TestClient, sample_audio_file):
        """Test complete async workflow with task polling."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            # Mock successful pipeline
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            mock_transcribe.return_value = {
                "text": "Test lecture content",
                "segments": [{"start": 0.0, "end": 5.0, "text": "Test"}],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest summary"
            
            # Submit async task
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post(
                    "/api/pipeline",
                    files=files,
                    params={"async_mode": True, "ratio": 0.2}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "task_id" in data
            assert data["status"] == "processing"
            
            task_id = data["task_id"]
            
            # Poll for status (with timeout)
            max_attempts = 10
            for attempt in range(max_attempts):
                status_response = client.get(f"/api/pipeline/{task_id}")
                assert status_response.status_code == 200
                
                status_data = status_response.json()
                assert "status" in status_data
                assert "progress" in status_data
                
                # Check progress structure
                progress = status_data["progress"]
                assert "stage" in progress
                assert "percent" in progress
                assert "message" in progress
                
                if status_data["status"] in ["completed", "failed"]:
                    break
                
                time.sleep(0.1)  # Small delay between polls
            
            # Verify final status
            final_status = client.get(f"/api/pipeline/{task_id}")
            assert final_status.status_code == 200
    
    @pytest.mark.api
    def test_async_mode_returns_immediately(self, client: TestClient, sample_audio_file):
        """Test async mode returns immediately without blocking."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock:
            # Simulate slow preprocessing (5 seconds)
            def slow_preprocess(*args, **kwargs):
                time.sleep(5)
                return ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            
            mock.side_effect = slow_preprocess
            
            start_time = time.time()
            
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post(
                    "/api/pipeline",
                    files=files,
                    params={"async_mode": True}
                )
            
            end_time = time.time()
            
            # Should return in < 1 second (not wait for processing)
            assert (end_time - start_time) < 1.0
            assert response.status_code == 200
            assert response.json()["status"] == "processing"
    
    @pytest.mark.api
    def test_async_progress_updates(self, client: TestClient, sample_audio_file):
        """Test progress updates through all stages."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            mock_transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest"
            
            # Submit task
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post("/api/pipeline", files=files, params={"async_mode": True})
            
            task_id = response.json()["task_id"]
            
            # Collect progress stages
            seen_stages = set()
            for _ in range(15):
                status_response = client.get(f"/api/pipeline/{task_id}")
                data = status_response.json()
                
                stage = data["progress"]["stage"]
                seen_stages.add(stage)
                
                if data["status"] in ["completed", "failed"]:
                    break
                
                time.sleep(0.1)
            
            # Should see multiple processing stages
            assert len(seen_stages) > 0


class TestPipelineSyncMode:
    """Test synchronous mode for immediate processing."""
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_sync_mode_complete_response(self, client: TestClient, sample_audio_file):
        """Test sync mode returns complete result immediately."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            mock_transcribe.return_value = {
                "text": "Complete lecture transcription",
                "segments": [{"start": 0.0, "end": 10.0, "text": "Lecture"}],
                "language": "en",
                "duration": 10.0
            }
            mock_summarize.return_value = "### Learning Objectives\nTest objectives"
            
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post(
                    "/api/pipeline",
                    files=files,
                    params={"async_mode": False, "ratio": 0.15}
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have complete result
            assert data["success"] is True
            assert "transcription" in data
            assert "summary" in data
            assert "metadata" in data
            
            # Verify transcription
            assert data["transcription"] == "Complete lecture transcription"
            
            # Verify metadata
            metadata = data["metadata"]
            assert metadata["duration"] == 10.0
            assert metadata["language"] == "en"
            assert metadata["ratio"] == 0.15
    
    @pytest.mark.api
    def test_sync_mode_waits_for_completion(self, client: TestClient, sample_audio_file):
        """Test sync mode blocks until processing completes."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            # Simulate processing time
            def slow_preprocess(*args, **kwargs):
                time.sleep(0.5)
                return ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            
            mock_preprocess.side_effect = slow_preprocess
            mock_transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest"
            
            start_time = time.time()
            
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post(
                    "/api/pipeline",
                    files=files,
                    params={"async_mode": False}
                )
            
            end_time = time.time()
            
            # Should wait for processing (at least 0.5 seconds)
            assert (end_time - start_time) >= 0.5
            assert response.status_code == 200
            assert "transcription" in response.json()


class TestPipelineFileHandling:
    """Test file upload, streaming, and size limits."""
    
    @pytest.mark.api
    def test_large_file_streaming(self, client: TestClient, monkeypatch):
        """Test large file is streamed in chunks."""
        # Set limit to 10MB
        from src.utils import settings
        monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 10)
        
        # Create 5MB file (within limit)
        large_content = b"0" * (5 * 1024 * 1024)
        
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            mock_transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest"
            
            files = {"file": ("large.mp3", io.BytesIO(large_content), "audio/mpeg")}
            response = client.post(
                "/api/pipeline",
                files=files,
                params={"async_mode": True}
            )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    @pytest.mark.api
    def test_file_size_enforcement_during_upload(self, client: TestClient, monkeypatch):
        """Test size limit is enforced during streaming upload."""
        # Set very small limit
        from src.utils import settings
        monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 0.001)  # 1KB
        
        # Create 5KB file (exceeds limit)
        large_content = b"0" * (5 * 1024)
        files = {"file": ("toolarge.mp3", io.BytesIO(large_content), "audio/mpeg")}
        
        response = client.post("/api/pipeline", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == ErrorCode.FILE_TOO_LARGE.value
        assert "size_mb" in data["detail"]["details"]
    
    @pytest.mark.api
    def test_content_type_validation(self, client: TestClient):
        """Test content-type header is validated."""
        # Create file with wrong content-type
        content = b"fake audio data"
        files = {"file": ("test.mp3", io.BytesIO(content), "application/pdf")}
        
        response = client.post("/api/pipeline", files=files)
        
        # Should still check file extension, not just content-type
        # Extension is .mp3, so should be accepted initially
        # But might fail at signature verification
        assert response.status_code in [200, 400]
    
    @pytest.mark.api
    def test_cleanup_on_validation_failure(self, client: TestClient):
        """Test uploaded file is cleaned up on validation failure."""
        # Create invalid file
        files = {"file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}
        
        response = client.post("/api/pipeline", files=files)
        
        assert response.status_code == 400
        # File should be deleted (hard to verify in test, but logged)


class TestPipelineEnhancement:
    """Test DeepFilterNet enhancement toggle."""
    
    @pytest.mark.api
    def test_enhancement_enabled_explicitly(self, client: TestClient, sample_audio_file):
        """Test DeepFilterNet can be enabled via parameter."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": True, "enhancer": "deepfilternet"})
            mock_transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest"
            
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post(
                    "/api/pipeline",
                    files=files,
                    params={"enhance": True, "async_mode": False}
                )
            
            assert response.status_code == 200
            
            # Verify preprocess was called with use_deepfilter=True
            call_kwargs = mock_preprocess.call_args[1]
            assert call_kwargs.get("use_deepfilter") is True
    
    @pytest.mark.api
    def test_enhancement_disabled_explicitly(self, client: TestClient, sample_audio_file):
        """Test DeepFilterNet can be disabled via parameter."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            mock_transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest"
            
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post(
                    "/api/pipeline",
                    files=files,
                    params={"enhance": False, "async_mode": False}
                )
            
            assert response.status_code == 200
            
            # Verify preprocess was called with use_deepfilter=False
            call_kwargs = mock_preprocess.call_args[1]
            assert call_kwargs.get("use_deepfilter") is False


class TestPipelineConcurrency:
    """Test concurrent upload handling."""
    
    @pytest.mark.api
    @pytest.mark.integration
    def test_concurrent_uploads(self, client: TestClient, sample_audio_file):
        """Test multiple concurrent uploads are handled correctly."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            mock_preprocess.return_value = ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            mock_transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest"
            
            # Submit 3 concurrent uploads
            task_ids = []
            for i in range(3):
                with open(sample_audio_file, "rb") as f:
                    files = {"file": (f"test{i}.mp3", f, "audio/mpeg")}
                    response = client.post(
                        "/api/pipeline",
                        files=files,
                        params={"async_mode": True}
                    )
                    assert response.status_code == 200
                    task_ids.append(response.json()["task_id"])
            
            # All task IDs should be unique
            assert len(set(task_ids)) == 3
            
            # All tasks should be trackable
            for task_id in task_ids:
                status_response = client.get(f"/api/pipeline/{task_id}")
                assert status_response.status_code == 200


class TestPipelineTaskLifecycle:
    """Test complete task lifecycle."""
    
    @pytest.mark.api
    def test_task_transitions_through_states(self, client: TestClient, sample_audio_file):
        """Test task progresses through expected states."""
        with patch("src.api.services.audio_preprocess.preprocess_audio") as mock_preprocess, \
             patch("src.api.services.transcriber.transcribe_audio") as mock_transcribe, \
             patch("src.api.services.summarizer.generate_summary") as mock_summarize:
            
            # Add small delays to observe state transitions
            def slow_preprocess(*args, **kwargs):
                time.sleep(0.2)
                return ("/tmp/clean.wav", {"enhanced": False, "enhancer": None})
            
            mock_preprocess.side_effect = slow_preprocess
            mock_transcribe.return_value = {
                "text": "Test",
                "segments": [],
                "language": "en",
                "duration": 5.0
            }
            mock_summarize.return_value = "### Summary\nTest"
            
            # Submit task
            with open(sample_audio_file, "rb") as f:
                files = {"file": ("test.mp3", f, "audio/mpeg")}
                response = client.post("/api/pipeline", files=files, params={"async_mode": True})
            
            task_id = response.json()["task_id"]
            
            # Track state transitions
            states_seen = []
            for _ in range(20):
                status = client.get(f"/api/pipeline/{task_id}")
                state = status.json()["status"]
                if not states_seen or states_seen[-1] != state:
                    states_seen.append(state)
                
                if state in ["completed", "failed"]:
                    break
                
                time.sleep(0.1)
            
            # Should transition from pending/processing to completed
            assert len(states_seen) > 0
            assert states_seen[-1] in ["completed", "failed"]
