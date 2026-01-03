"""Unit tests for Whisper transcription service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.api.services import transcriber
from src.utils.errors import ProcessingError, ErrorCode


class MockSegment:
    """Mock Whisper segment."""
    def __init__(self, start, end, text, avg_logprob=-0.5):
        self.start = start
        self.end = end
        self.text = text
        self.avg_logprob = avg_logprob


class MockTranscriptionInfo:
    """Mock Whisper transcription info."""
    def __init__(self, language="en", duration=120.0):
        self.language = language
        self.duration = duration


class TestWhisperModelLoading:
    """Test Whisper model initialization."""
    
    def test_lazy_model_loading(self, monkeypatch):
        """Test model is not loaded until first use."""
        # Reset global model
        transcriber._model = None
        
        mock_whisper = Mock()
        monkeypatch.setattr("src.api.services.transcriber.WhisperModel", mock_whisper)
        
        # Model should not be loaded yet
        assert transcriber._model is None
        
        # Get model should trigger loading
        model = transcriber.get_model()
        assert model is not None
        assert mock_whisper.called
    
    def test_model_reuse(self, monkeypatch):
        """Test model is loaded only once and reused."""
        # Reset and set up mock
        transcriber._model = None
        mock_whisper = Mock()
        mock_instance = Mock()
        mock_whisper.return_value = mock_instance
        monkeypatch.setattr("src.api.services.transcriber.WhisperModel", mock_whisper)
        
        # Get model twice
        model1 = transcriber.get_model()
        model2 = transcriber.get_model()
        
        # Should be same instance
        assert model1 is model2
        # Constructor called only once
        assert mock_whisper.call_count == 1
    
    def test_model_load_failure(self, monkeypatch):
        """Test handling of model load failure."""
        transcriber._model = None
        
        def raise_error(*args, **kwargs):
            raise RuntimeError("Model not found")
        
        monkeypatch.setattr("src.api.services.transcriber.WhisperModel", raise_error)
        
        with pytest.raises(ProcessingError) as exc_info:
            transcriber.get_model()
        
        assert exc_info.value.error_code == ErrorCode.WHISPER_MODEL_LOAD_FAILED
        assert "Could not load Whisper model" in exc_info.value.message


class TestTranscription:
    """Test audio transcription."""
    
    @pytest.fixture
    def mock_model(self, monkeypatch):
        """Mock Whisper model for testing."""
        mock = MagicMock()
        transcriber._model = mock
        return mock
    
    def test_transcribe_basic_audio(self, mock_model, tmp_path):
        """Test basic transcription with simple audio."""
        # Create test audio file path
        audio_path = str(tmp_path / "test.mp3")
        
        # Mock transcription response
        segments = [
            MockSegment(0.0, 5.0, "Hello world", -0.3),
            MockSegment(5.0, 10.0, "This is a test", -0.4)
        ]
        info = MockTranscriptionInfo(language="en", duration=10.0)
        
        mock_model.transcribe.return_value = (iter(segments), info)
        
        # Transcribe
        result = transcriber.transcribe_audio(audio_path)
        
        # Verify result structure
        assert "text" in result
        assert "segments" in result
        assert "language" in result
        assert "duration" in result
        
        # Verify content
        assert result["text"] == "Hello world This is a test"
        assert result["language"] == "en"
        assert result["duration"] == 10.0
        assert len(result["segments"]) == 2
        
        # Verify first segment
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 5.0
        assert result["segments"][0]["text"] == "Hello world"
        assert "confidence" in result["segments"][0]
    
    def test_transcribe_empty_audio(self, mock_model, tmp_path):
        """Test transcription of silent/empty audio."""
        audio_path = str(tmp_path / "silent.mp3")
        
        # Mock empty transcription
        segments = []
        info = MockTranscriptionInfo(language="en", duration=5.0)
        
        mock_model.transcribe.return_value = (iter(segments), info)
        
        result = transcriber.transcribe_audio(audio_path)
        
        assert result["text"] == ""
        assert result["segments"] == []
        assert result["duration"] == 5.0
    
    def test_transcribe_multi_language(self, mock_model, tmp_path):
        """Test multi-language detection."""
        audio_path = str(tmp_path / "spanish.mp3")
        
        segments = [
            MockSegment(0.0, 3.0, "Hola mundo", -0.2)
        ]
        info = MockTranscriptionInfo(language="es", duration=3.0)
        
        mock_model.transcribe.return_value = (iter(segments), info)
        
        result = transcriber.transcribe_audio(audio_path)
        
        assert result["language"] == "es"
        assert result["text"] == "Hola mundo"
    
    def test_transcribe_long_audio(self, mock_model, tmp_path):
        """Test transcription of long audio with many segments."""
        audio_path = str(tmp_path / "lecture.mp3")
        
        # Generate many segments
        segments = [
            MockSegment(i * 10.0, (i + 1) * 10.0, f"Segment {i}", -0.5)
            for i in range(100)
        ]
        info = MockTranscriptionInfo(language="en", duration=1000.0)
        
        mock_model.transcribe.return_value = (iter(segments), info)
        
        result = transcriber.transcribe_audio(audio_path)
        
        assert len(result["segments"]) == 100
        assert result["duration"] == 1000.0
        # Check text concatenation
        assert "Segment 0" in result["text"]
        assert "Segment 99" in result["text"]
    
    def test_transcribe_with_timestamps(self, mock_model, tmp_path):
        """Test segment timestamps are properly formatted."""
        audio_path = str(tmp_path / "test.mp3")
        
        segments = [
            MockSegment(0.123, 5.678, "Test segment", -0.456)
        ]
        info = MockTranscriptionInfo(language="en", duration=5.678)
        
        mock_model.transcribe.return_value = (iter(segments), info)
        
        result = transcriber.transcribe_audio(audio_path)
        
        # Check rounding to 2 decimal places
        assert result["segments"][0]["start"] == 0.12
        assert result["segments"][0]["end"] == 5.68
        # Duration also rounded
        assert result["duration"] == 5.68
        # Confidence rounded to 3 decimals
        assert result["segments"][0]["confidence"] == -0.456
    
    def test_transcribe_with_whitespace(self, mock_model, tmp_path):
        """Test handling of segments with extra whitespace."""
        audio_path = str(tmp_path / "test.mp3")
        
        segments = [
            MockSegment(0.0, 5.0, "  Hello  ", -0.3),
            MockSegment(5.0, 10.0, "\n  world  \n", -0.4)
        ]
        info = MockTranscriptionInfo(language="en", duration=10.0)
        
        mock_model.transcribe.return_value = (iter(segments), info)
        
        result = transcriber.transcribe_audio(audio_path)
        
        # Whitespace should be stripped
        assert result["text"] == "Hello world"
        assert result["segments"][0]["text"] == "Hello"
        assert result["segments"][1]["text"] == "world"


class TestTranscriptionErrors:
    """Test error handling in transcription."""
    
    @pytest.fixture
    def mock_model(self, monkeypatch):
        """Mock Whisper model."""
        mock = MagicMock()
        transcriber._model = mock
        return mock
    
    def test_transcribe_model_error(self, mock_model, tmp_path):
        """Test handling of model transcription errors."""
        audio_path = str(tmp_path / "corrupt.mp3")
        
        # Mock transcription failure
        mock_model.transcribe.side_effect = RuntimeError("Decoding failed")
        
        with pytest.raises(ProcessingError) as exc_info:
            transcriber.transcribe_audio(audio_path)
        
        assert exc_info.value.error_code == ErrorCode.TRANSCRIPTION_FAILED
        assert "Failed to transcribe audio" in exc_info.value.message
    
    def test_transcribe_io_error(self, mock_model, tmp_path):
        """Test handling of I/O errors."""
        audio_path = str(tmp_path / "nonexistent.mp3")
        
        # Mock file not found
        mock_model.transcribe.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(ProcessingError) as exc_info:
            transcriber.transcribe_audio(audio_path)
        
        assert exc_info.value.error_code == ErrorCode.TRANSCRIPTION_FAILED
    
    def test_transcribe_unexpected_error(self, mock_model, tmp_path):
        """Test handling of unexpected errors."""
        audio_path = str(tmp_path / "test.mp3")
        
        # Mock unexpected error
        mock_model.transcribe.side_effect = Exception("Unexpected error")
        
        with pytest.raises(ProcessingError) as exc_info:
            transcriber.transcribe_audio(audio_path)
        
        assert exc_info.value.error_code == ErrorCode.TRANSCRIPTION_FAILED


class TestTranscriptionConfiguration:
    """Test transcription configuration."""
    
    @pytest.fixture
    def mock_model(self, monkeypatch):
        """Mock Whisper model."""
        mock = MagicMock()
        transcriber._model = mock
        return mock
    
    def test_transcribe_uses_vad_filter(self, mock_model, tmp_path):
        """Test VAD filter is enabled in transcription."""
        audio_path = str(tmp_path / "test.mp3")
        
        segments = [MockSegment(0.0, 5.0, "Test", -0.3)]
        info = MockTranscriptionInfo()
        mock_model.transcribe.return_value = (iter(segments), info)
        
        transcriber.transcribe_audio(audio_path)
        
        # Verify VAD filter is enabled
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs.get("vad_filter") is True
    
    def test_transcribe_uses_word_timestamps(self, mock_model, tmp_path):
        """Test word timestamps are enabled."""
        audio_path = str(tmp_path / "test.mp3")
        
        segments = [MockSegment(0.0, 5.0, "Test", -0.3)]
        info = MockTranscriptionInfo()
        mock_model.transcribe.return_value = (iter(segments), info)
        
        transcriber.transcribe_audio(audio_path)
        
        # Verify word timestamps enabled
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs.get("word_timestamps") is True
