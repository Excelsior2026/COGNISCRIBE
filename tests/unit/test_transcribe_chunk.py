"""Unit tests for chunk transcription endpoint."""

import pytest
import base64
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from src.main import app


class TestChunkTranscription:
    """Test basic chunk transcription functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_audio_chunk(self):
        """Create mock audio chunk data."""
        # Simulate small audio data (1KB)
        audio_data = b"\x00" * 1024
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
        return audio_b64
    
    @patch('src.api.routers.transcribe_chunk.transcriber.transcribe_audio')
    def test_transcribe_single_chunk(self, mock_transcribe, client, mock_audio_chunk):
        """Test transcribing a single audio chunk."""
        mock_transcribe.return_value = {
            "text": "This is a test transcription.",
            "segments": [],
            "language": "en",
            "duration": 1.0
        }
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": mock_audio_chunk,
                "timestamp": 5,
                "mime_type": "audio/webm"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "This is a test transcription."
        assert data["timestamp"] == 5
    
    @patch('src.api.routers.transcribe_chunk.transcriber.transcribe_audio')
    def test_chunk_with_mp3_mime_type(self, mock_transcribe, client, mock_audio_chunk):
        """Test chunk with MP3 MIME type."""
        mock_transcribe.return_value = {"text": "Test", "segments": [], "language": "en", "duration": 1.0}
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": mock_audio_chunk,
                "timestamp": 0,
                "mime_type": "audio/mpeg"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify temp file had .mp3 extension
        call_args = mock_transcribe.call_args[0]
        temp_path = call_args[0]
        assert temp_path.endswith(".mp3")
    
    @patch('src.api.routers.transcribe_chunk.transcriber.transcribe_audio')
    def test_chunk_with_m4a_mime_type(self, mock_transcribe, client, mock_audio_chunk):
        """Test chunk with M4A MIME type."""
        mock_transcribe.return_value = {"text": "Test", "segments": [], "language": "en", "duration": 1.0}
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": mock_audio_chunk,
                "timestamp": 10,
                "mime_type": "audio/mp4"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify temp file had .m4a extension
        call_args = mock_transcribe.call_args[0]
        temp_path = call_args[0]
        assert temp_path.endswith(".m4a")
    
    @patch('src.api.routers.transcribe_chunk.transcriber.transcribe_audio')
    def test_chunk_with_ogg_mime_type(self, mock_transcribe, client, mock_audio_chunk):
        """Test chunk with OGG MIME type."""
        mock_transcribe.return_value = {"text": "Test", "segments": [], "language": "en", "duration": 1.0}
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": mock_audio_chunk,
                "timestamp": 15,
                "mime_type": "audio/ogg"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify temp file had .ogg extension
        call_args = mock_transcribe.call_args[0]
        temp_path = call_args[0]
        assert temp_path.endswith(".ogg")


class TestChunkValidation:
    """Test chunk validation and error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_invalid_base64(self, client):
        """Test handling of invalid base64 data."""
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": "not-valid-base64!!!",
                "timestamp": 0,
                "mime_type": "audio/webm"
            }
        )
        
        assert response.status_code == 200  # Graceful degradation
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "invalid_audio_chunk"
        assert data["text"] == ""
    
    def test_oversized_chunk_before_decode(self, client, monkeypatch):
        """Test rejection of oversized chunk (detected before decode)."""
        # Set very small limit
        from src.utils import settings
        monkeypatch.setattr(settings, "MAX_CHUNK_BYTES", 100)  # 100 bytes
        
        # Create chunk larger than limit
        large_audio = b"\x00" * 200
        large_b64 = base64.b64encode(large_audio).decode("utf-8")
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": large_b64,
                "timestamp": 0,
                "mime_type": "audio/webm"
            }
        )
        
        assert response.status_code == 200  # Graceful degradation
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "chunk_too_large"
    
    def test_oversized_chunk_after_decode(self, client, monkeypatch):
        """Test rejection of oversized chunk (detected after decode)."""
        from src.utils import settings
        monkeypatch.setattr(settings, "MAX_CHUNK_BYTES", 500)
        
        # Create chunk that appears small in base64 but is large decoded
        large_audio = b"\x00" * 600
        large_b64 = base64.b64encode(large_audio).decode("utf-8")
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": large_b64,
                "timestamp": 0,
                "mime_type": "audio/webm"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "chunk_too_large"
    
    def test_empty_audio_chunk(self, client):
        """Test handling of empty audio data."""
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": "",
                "timestamp": 0,
                "mime_type": "audio/webm"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # Empty chunk should be rejected or handled gracefully
        assert data["success"] is False


class TestChunkErrorHandling:
    """Test error handling and graceful degradation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_audio_chunk(self):
        """Create mock audio chunk."""
        audio_data = b"\x00" * 1024
        return base64.b64encode(audio_data).decode("utf-8")
    
    @patch('src.api.routers.transcribe_chunk.transcriber.transcribe_audio')
    def test_transcription_error_graceful_degradation(self, mock_transcribe, client, mock_audio_chunk):
        """Test graceful degradation when transcription fails."""
        mock_transcribe.side_effect = RuntimeError("Whisper model error")
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": mock_audio_chunk,
                "timestamp": 5,
                "mime_type": "audio/webm"
            }
        )
        
        # Should return 200 with empty text (graceful degradation)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["text"] == ""
        assert data["error"] == "chunk_processing_failed"
        assert data["timestamp"] == 5
    
    @patch('src.api.routers.transcribe_chunk.transcriber.transcribe_audio')
    def test_timestamp_preserved_on_error(self, mock_transcribe, client, mock_audio_chunk):
        """Test timestamp is preserved even when transcription fails."""
        mock_transcribe.side_effect = Exception("Generic error")
        
        response = client.post(
            "/api/transcribe-chunk",
            json={
                "audio": mock_audio_chunk,
                "timestamp": 42,
                "mime_type": "audio/webm"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["timestamp"] == 42


class TestChunkConcurrency:
    """Test concurrent chunk processing."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_audio_chunk(self):
        """Create mock audio chunk."""
        audio_data = b"\x00" * 1024
        return base64.b64encode(audio_data).decode("utf-8")
    
    @patch('src.api.routers.transcribe_chunk.transcriber.transcribe_audio')
    def test_multiple_chunks_concurrent(self, mock_transcribe, client, mock_audio_chunk):
        """Test multiple chunks can be processed concurrently."""
        # Return different text for each call
        mock_transcribe.side_effect = [
            {"text": "Chunk 1", "segments": [], "language": "en", "duration": 1.0},
            {"text": "Chunk 2", "segments": [], "language": "en", "duration": 1.0},
            {"text": "Chunk 3", "segments": [], "language": "en", "duration": 1.0},
        ]
        
        # Submit 3 chunks
        responses = []
        for i in range(3):
            response = client.post(
                "/api/transcribe-chunk",
                json={
                    "audio": mock_audio_chunk,
                    "timestamp": i * 5,
                    "mime_type": "audio/webm"
                }
            )
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["success"] is True for r in responses)
        
        # Each should have correct text
        texts = [r.json()["text"] for r in responses]
        assert texts == ["Chunk 1", "Chunk 2", "Chunk 3"]
        
        # Timestamps should be preserved
        timestamps = [r.json()["timestamp"] for r in responses]
        assert timestamps == [0, 5, 10]
