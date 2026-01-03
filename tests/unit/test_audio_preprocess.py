"""Unit tests for audio preprocessing service."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from src.api.services import audio_preprocess
from src.utils.errors import ProcessingError, ErrorCode


class TestAudioFormatConversion:
    """Test audio format handling and conversion."""
    
    @pytest.fixture
    def mock_audio_segment(self):
        """Mock AudioSegment for testing."""
        mock_segment = MagicMock()
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_segment.export.return_value = None
        return mock_segment
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.nr.reduce_noise')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    def test_preprocess_mp3_format(self, mock_normalize, mock_write, mock_nr, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test preprocessing MP3 audio file."""
        input_path = str(tmp_path / "test.mp3")
        
        # Mock audio loading and processing
        mock_load.return_value = mock_audio_segment
        mock_librosa.return_value = (Mock(), 16000)
        mock_nr.return_value = Mock()
        mock_normalize.return_value = Mock()
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            output_path, metadata = audio_preprocess.preprocess_audio(input_path)
        
        assert output_path.endswith('_clean.wav')
        assert os.path.dirname(output_path) == audio_preprocess.TEMP_AUDIO_DIR
        assert metadata["enhanced"] is False
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.nr.reduce_noise')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    def test_preprocess_wav_format(self, mock_normalize, mock_write, mock_nr, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test preprocessing WAV audio file."""
        input_path = str(tmp_path / "test.wav")
        
        mock_load.return_value = mock_audio_segment
        mock_librosa.return_value = (Mock(), 16000)
        mock_nr.return_value = Mock()
        mock_normalize.return_value = Mock()
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            output_path, metadata = audio_preprocess.preprocess_audio(input_path)
        
        assert output_path.endswith('_clean.wav')
        assert metadata["enhanced"] is False


class TestAudioProcessing:
    """Test audio processing pipeline."""
    
    @pytest.fixture
    def mock_audio_segment(self):
        """Mock AudioSegment for testing."""
        mock_segment = MagicMock()
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_segment.export.return_value = None
        return mock_segment
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.nr.reduce_noise')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    def test_mono_conversion(self, mock_normalize, mock_write, mock_nr, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test conversion to mono audio."""
        input_path = str(tmp_path / "stereo.mp3")
        
        mock_load.return_value = mock_audio_segment
        mock_librosa.return_value = (Mock(), 16000)
        mock_nr.return_value = Mock()
        mock_normalize.return_value = Mock()
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            audio_preprocess.preprocess_audio(input_path)
        
        # Verify mono conversion called
        mock_audio_segment.set_channels.assert_called_with(1)
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.nr.reduce_noise')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    def test_48khz_intermediate_conversion(self, mock_normalize, mock_write, mock_nr, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test intermediate conversion to 48kHz for DeepFilterNet."""
        input_path = str(tmp_path / "test.mp3")
        
        mock_load.return_value = mock_audio_segment
        mock_librosa.return_value = (Mock(), 16000)
        mock_nr.return_value = Mock()
        mock_normalize.return_value = Mock()
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            audio_preprocess.preprocess_audio(input_path)
        
        # Verify 48kHz conversion (first call), then 16kHz (second call)
        calls = mock_audio_segment.set_frame_rate.call_args_list
        assert calls[0] == call(48000)
        assert calls[1] == call(16000)
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.nr.reduce_noise')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    def test_noise_reduction_applied(self, mock_normalize, mock_write, mock_nr, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test noise reduction is applied."""
        input_path = str(tmp_path / "noisy.mp3")
        
        mock_load.return_value = mock_audio_segment
        mock_audio_data = Mock()
        mock_librosa.return_value = (mock_audio_data, 16000)
        mock_nr.return_value = mock_audio_data
        mock_normalize.return_value = mock_audio_data
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            audio_preprocess.preprocess_audio(input_path)
        
        # Verify noise reduction was called
        mock_nr.assert_called_once()
        # Verify normalization was called
        mock_normalize.assert_called_once_with(mock_audio_data)
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    def test_output_saved_correctly(self, mock_normalize, mock_write, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test processed audio is saved."""
        input_path = str(tmp_path / "test.mp3")
        
        mock_load.return_value = mock_audio_segment
        mock_audio_data = Mock()
        mock_librosa.return_value = (mock_audio_data, 16000)
        mock_normalize.return_value = mock_audio_data
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            output_path, _ = audio_preprocess.preprocess_audio(input_path)
        
        # Verify soundfile write was called
        mock_write.assert_called_once_with(output_path, mock_audio_data, 16000)


class TestDeepFilterNet:
    """Test DeepFilterNet integration."""
    
    @pytest.fixture
    def mock_audio_segment(self):
        """Mock AudioSegment for testing."""
        mock_segment = MagicMock()
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_segment.export.return_value = None
        return mock_segment
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    @patch('src.api.services.audio_preprocess.run_deepfilternet')
    def test_deepfilternet_enabled(self, mock_df, mock_normalize, mock_write, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test DeepFilterNet is used when enabled."""
        input_path = str(tmp_path / "test.mp3")
        enhanced_path = str(tmp_path / "enhanced.wav")
        
        mock_load.return_value = mock_audio_segment
        mock_librosa.return_value = (Mock(), 16000)
        mock_normalize.return_value = Mock()
        # Mock successful DeepFilterNet enhancement
        mock_df.return_value = (enhanced_path, None)
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', True):
            output_path, metadata = audio_preprocess.preprocess_audio(input_path)
        
        assert metadata["enhanced"] is True
        assert metadata["enhancer"] == "deepfilternet"
        mock_df.assert_called_once()
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.nr.reduce_noise')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    @patch('src.api.services.audio_preprocess.run_deepfilternet')
    def test_deepfilternet_fallback(self, mock_df, mock_normalize, mock_write, mock_nr, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test fallback when DeepFilterNet fails."""
        input_path = str(tmp_path / "test.mp3")
        
        mock_load.return_value = mock_audio_segment
        mock_librosa.return_value = (Mock(), 16000)
        mock_nr.return_value = Mock()
        mock_normalize.return_value = Mock()
        # Mock DeepFilterNet failure
        mock_df.return_value = (None, None)
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', True):
            output_path, metadata = audio_preprocess.preprocess_audio(input_path)
        
        # Should fall back to standard preprocessing
        assert metadata["enhanced"] is False
        mock_nr.assert_called_once()  # Standard noise reduction used
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    @patch('src.api.services.audio_preprocess.sf.write')
    @patch('src.api.services.audio_preprocess.librosa.util.normalize')
    def test_deepfilternet_disabled(self, mock_normalize, mock_write, mock_librosa, mock_load, mock_audio_segment, tmp_path):
        """Test DeepFilterNet is skipped when disabled."""
        input_path = str(tmp_path / "test.mp3")
        
        mock_load.return_value = mock_audio_segment
        mock_librosa.return_value = (Mock(), 16000)
        mock_normalize.return_value = Mock()
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            output_path, metadata = audio_preprocess.preprocess_audio(input_path)
        
        assert metadata["enhanced"] is False
        assert metadata["enhancer"] is None
    
    @patch('src.api.services.audio_preprocess.resolve_deepfilternet_bin')
    def test_resolve_deepfilternet_binary(self, mock_resolve):
        """Test DeepFilterNet binary resolution."""
        mock_resolve.return_value = "/usr/local/bin/deepfilter"
        
        result = audio_preprocess.resolve_deepfilternet_bin()
        assert result == "/usr/local/bin/deepfilter"
    
    @patch('src.api.services.audio_preprocess.resolve_deepfilternet_bin')
    def test_resolve_deepfilternet_not_found(self, mock_resolve):
        """Test handling when DeepFilterNet binary not found."""
        mock_resolve.return_value = None
        
        result, _ = audio_preprocess.run_deepfilternet("/tmp/test.wav")
        assert result is None


class TestErrorHandling:
    """Test error handling in audio preprocessing."""
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    def test_corrupted_audio_file(self, mock_load, tmp_path):
        """Test handling of corrupted audio file."""
        input_path = str(tmp_path / "corrupted.mp3")
        
        # Mock file corruption error
        mock_load.side_effect = Exception("Invalid audio format")
        
        with pytest.raises(ProcessingError) as exc_info:
            audio_preprocess.preprocess_audio(input_path)
        
        assert exc_info.value.error_code == ErrorCode.PREPROCESSING_FAILED
        assert "Failed to preprocess audio" in exc_info.value.message
    
    @patch('src.api.services.audio_preprocess._load_audio_segment')
    @patch('src.api.services.audio_preprocess.librosa.load')
    def test_librosa_load_failure(self, mock_librosa, mock_load, tmp_path):
        """Test handling of librosa load failure."""
        input_path = str(tmp_path / "test.mp3")
        
        mock_segment = MagicMock()
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_load.return_value = mock_segment
        
        # Mock librosa failure
        mock_librosa.side_effect = Exception("Cannot load audio")
        
        with patch('src.api.services.audio_preprocess.DEEPFILTERNET_ENABLED', False):
            with pytest.raises(ProcessingError) as exc_info:
                audio_preprocess.preprocess_audio(input_path)
        
        assert exc_info.value.error_code == ErrorCode.PREPROCESSING_FAILED


class TestTempFileCleanup:
    """Test temporary file cleanup."""
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_temp_file(self, mock_remove, mock_exists):
        """Test successful temp file cleanup."""
        mock_exists.return_value = True
        
        audio_preprocess.cleanup_temp_file("/tmp/test.wav")
        
        mock_remove.assert_called_once_with("/tmp/test.wav")
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_nonexistent_file(self, mock_remove, mock_exists):
        """Test cleanup of non-existent file doesn't error."""
        mock_exists.return_value = False
        
        # Should not raise
        audio_preprocess.cleanup_temp_file("/tmp/nonexistent.wav")
        
        mock_remove.assert_not_called()
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_failure_handled(self, mock_remove, mock_exists):
        """Test cleanup failure is handled gracefully."""
        mock_exists.return_value = True
        mock_remove.side_effect = OSError("Permission denied")
        
        # Should not raise, just log warning
        audio_preprocess.cleanup_temp_file("/tmp/test.wav")
