"""Unit tests for input validation module."""
import pytest
import tempfile
import os
from src.utils.validation import (
    sanitize_filename,
    sanitize_subject,
    validate_file_extension,
    validate_file_size,
    validate_ratio,
    verify_file_signature,
)
from src.utils.errors import ValidationError, ErrorCode


class TestFilenameSanitization:
    """Test filename sanitization."""
    
    def test_basic_filename(self):
        """Should keep clean filenames unchanged."""
        assert sanitize_filename("lecture.mp3") == "lecture.mp3"
        assert sanitize_filename("biology_101.wav") == "biology_101.wav"
        assert sanitize_filename("Cardio-Lecture.m4a") == "Cardio-Lecture.m4a"
    
    def test_remove_path_traversal(self):
        """Should remove path traversal attempts."""
        assert sanitize_filename("../etc/passwd") == "etcpasswd"
        assert sanitize_filename("../../secret.txt") == "secret.txt"
        assert sanitize_filename("dir/../file.mp3") == "dirfile.mp3"
    
    def test_remove_absolute_paths(self):
        """Should remove absolute path components."""
        assert sanitize_filename("/etc/passwd") == "etcpasswd"
        assert sanitize_filename("/var/log/file.txt") == "varlogfile.txt"
    
    def test_remove_dangerous_characters(self):
        """Should remove dangerous characters."""
        # Null bytes
        assert "\x00" not in sanitize_filename("file\x00name.mp3")
        
        # Control characters
        assert "\n" not in sanitize_filename("file\nname.mp3")
        assert "\r" not in sanitize_filename("file\rname.mp3")
    
    def test_unicode_handling(self):
        """Should handle unicode filenames safely."""
        # Keep safe unicode
        result = sanitize_filename("讲座_音频.mp3")
        assert ".mp3" in result
        
        # Remove problematic unicode
        result = sanitize_filename("file\u202ename.mp3")  # Right-to-left override
        assert "\u202e" not in result
    
    def test_spaces_and_special_chars(self):
        """Should handle spaces and common special characters."""
        assert sanitize_filename("My Lecture (2024).mp3") == "My Lecture (2024).mp3"
        assert sanitize_filename("Biology - Part 1.wav") == "Biology - Part 1.wav"
    
    def test_empty_filename(self):
        """Should provide default for empty filename."""
        assert sanitize_filename("") == "audio"
        assert sanitize_filename("   ") == "audio"
    
    def test_extension_preserved(self):
        """Should preserve file extensions."""
        assert sanitize_filename("test.mp3").endswith(".mp3")
        assert sanitize_filename("test.WAV").endswith(".WAV")
    
    def test_very_long_filename(self):
        """Should truncate very long filenames."""
        long_name = "a" * 300 + ".mp3"
        result = sanitize_filename(long_name)
        
        # Should be truncated but keep extension
        assert len(result) <= 255
        assert result.endswith(".mp3")
    
    def test_multiple_extensions(self):
        """Should handle multiple dots in filename."""
        result = sanitize_filename("file.backup.mp3")
        assert result == "file.backup.mp3"


class TestSubjectSanitization:
    """Test subject/topic sanitization."""
    
    def test_basic_subject(self):
        """Should keep clean subjects unchanged."""
        assert sanitize_subject("Cardiology") == "Cardiology"
        assert sanitize_subject("Anatomy 101") == "Anatomy 101"
    
    def test_strip_whitespace(self):
        """Should strip leading/trailing whitespace."""
        assert sanitize_subject("  Biology  ") == "Biology"
        assert sanitize_subject("\tPhysics\n") == "Physics"
    
    def test_none_subject(self):
        """Should handle None gracefully."""
        assert sanitize_subject(None) is None
    
    def test_empty_subject(self):
        """Should return None for empty subject."""
        assert sanitize_subject("") is None
        assert sanitize_subject("   ") is None
    
    def test_very_long_subject(self):
        """Should truncate very long subjects."""
        long_subject = "a" * 200
        result = sanitize_subject(long_subject)
        
        assert len(result) <= 100
    
    def test_remove_control_characters(self):
        """Should remove control characters from subject."""
        result = sanitize_subject("Biology\n\rLecture")
        assert "\n" not in result
        assert "\r" not in result


class TestFileExtensionValidation:
    """Test file extension validation."""
    
    def test_valid_extensions(self):
        """Should accept valid audio extensions."""
        valid_files = [
            "audio.mp3",
            "lecture.wav",
            "recording.m4a",
            "test.flac",
            "file.ogg",
            "audio.aac",
        ]
        
        for filename in valid_files:
            ext = validate_file_extension(filename)
            assert ext.startswith(".")
    
    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert validate_file_extension("file.MP3") == ".mp3"
        assert validate_file_extension("file.WaV") == ".wav"
        assert validate_file_extension("file.M4A") == ".m4a"
    
    def test_invalid_extension(self):
        """Should reject invalid extensions."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension("document.pdf")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_FILE_TYPE
        assert "pdf" in str(exc_info.value.message).lower()
    
    def test_no_extension(self):
        """Should reject files without extension."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension("audio_file")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_FILE_TYPE
    
    def test_hidden_file(self):
        """Should reject hidden files without extension."""
        with pytest.raises(ValidationError):
            validate_file_extension(".hidden")
    
    def test_multiple_dots(self):
        """Should use last extension with multiple dots."""
        ext = validate_file_extension("file.backup.mp3")
        assert ext == ".mp3"


class TestFileSizeValidation:
    """Test file size validation."""
    
    def test_valid_size(self):
        """Should accept files within size limit."""
        # 1 MB
        validate_file_size(1024 * 1024)
        
        # 500 MB
        validate_file_size(500 * 1024 * 1024)
        
        # Just under limit (999 MB)
        validate_file_size(999 * 1024 * 1024)
    
    def test_zero_size(self):
        """Should reject zero-sized files."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(0)
        
        assert exc_info.value.error_code == ErrorCode.FILE_TOO_SMALL
    
    def test_negative_size(self):
        """Should reject negative sizes."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(-1)
        
        assert exc_info.value.error_code == ErrorCode.FILE_TOO_SMALL
    
    def test_too_large(self):
        """Should reject files exceeding size limit."""
        # Slightly over 1000 MB limit
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(1001 * 1024 * 1024)
        
        assert exc_info.value.error_code == ErrorCode.FILE_TOO_LARGE
        assert "1001" in str(exc_info.value.message) or "too large" in str(exc_info.value.message).lower()
    
    def test_boundary_cases(self):
        """Should handle exact boundary values."""
        # Exactly at limit (1000 MB)
        validate_file_size(1000 * 1024 * 1024)
        
        # 1 byte
        validate_file_size(1)


class TestRatioValidation:
    """Test ratio validation."""
    
    def test_valid_ratios(self):
        """Should accept valid ratios."""
        assert validate_ratio(0.15) == 0.15
        assert validate_ratio(0.05) == 0.05
        assert validate_ratio(1.0) == 1.0
        assert validate_ratio(0.5) == 0.5
    
    def test_round_to_precision(self):
        """Should round ratios to 2 decimal places."""
        assert validate_ratio(0.155) == 0.15
        assert validate_ratio(0.156) == 0.16
        assert validate_ratio(0.333) == 0.33
    
    def test_below_minimum(self):
        """Should reject ratios below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            validate_ratio(0.04)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_RATIO
        assert "0.05" in str(exc_info.value.message)
    
    def test_above_maximum(self):
        """Should reject ratios above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            validate_ratio(1.1)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_RATIO
    
    def test_negative_ratio(self):
        """Should reject negative ratios."""
        with pytest.raises(ValidationError) as exc_info:
            validate_ratio(-0.5)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_RATIO
    
    def test_boundary_cases(self):
        """Should handle exact boundaries."""
        assert validate_ratio(0.05) == 0.05
        assert validate_ratio(1.0) == 1.0


class TestFileSignatureVerification:
    """Test file signature (magic number) verification."""
    
    def test_mp3_signature(self):
        """Should verify MP3 file signatures."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            # MP3 with ID3 tag
            f.write(b"ID3\x03\x00\x00\x00\x00")
            f.write(b"\x00" * 100)
            temp_path = f.name
        
        try:
            assert verify_file_signature(temp_path, ".mp3") is True
        finally:
            os.unlink(temp_path)
    
    def test_wav_signature(self):
        """Should verify WAV file signatures."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # RIFF header
            f.write(b"RIFF")
            f.write(b"\x00\x00\x00\x00")  # File size
            f.write(b"WAVE")
            f.write(b"\x00" * 100)
            temp_path = f.name
        
        try:
            assert verify_file_signature(temp_path, ".wav") is True
        finally:
            os.unlink(temp_path)
    
    def test_flac_signature(self):
        """Should verify FLAC file signatures."""
        with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as f:
            f.write(b"fLaC")
            f.write(b"\x00" * 100)
            temp_path = f.name
        
        try:
            assert verify_file_signature(temp_path, ".flac") is True
        finally:
            os.unlink(temp_path)
    
    def test_ogg_signature(self):
        """Should verify OGG file signatures."""
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(b"OggS")
            f.write(b"\x00" * 100)
            temp_path = f.name
        
        try:
            assert verify_file_signature(temp_path, ".ogg") is True
        finally:
            os.unlink(temp_path)
    
    def test_wrong_signature(self):
        """Should detect wrong file signature."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            # Write PDF header instead
            f.write(b"%PDF-1.4")
            f.write(b"\x00" * 100)
            temp_path = f.name
        
        try:
            assert verify_file_signature(temp_path, ".mp3") is False
        finally:
            os.unlink(temp_path)
    
    def test_empty_file(self):
        """Should handle empty files gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
        
        try:
            # Empty file has no signature
            assert verify_file_signature(temp_path, ".mp3") is False
        finally:
            os.unlink(temp_path)
    
    def test_unsupported_format(self):
        """Should return True for unsupported formats (no verification)."""
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(b"random data")
            temp_path = f.name
        
        try:
            # No signature check for .webm, should pass
            assert verify_file_signature(temp_path, ".webm") is True
        finally:
            os.unlink(temp_path)
    
    def test_nonexistent_file(self):
        """Should handle nonexistent files gracefully."""
        result = verify_file_signature("/nonexistent/file.mp3", ".mp3")
        assert result is False


class TestValidationEdgeCases:
    """Test edge cases and security scenarios."""
    
    def test_path_traversal_combinations(self):
        """Should block all path traversal attempts."""
        dangerous = [
            "..\\..\\windows\\system32\\file.mp3",
            "./../secret.mp3",
            "dir/../../etc/passwd.mp3",
            "....//....//file.mp3",
        ]
        
        for filename in dangerous:
            result = sanitize_filename(filename)
            # Should not contain path separators or ..
            assert ".." not in result
            assert "/" not in result
            assert "\\" not in result
    
    def test_null_byte_injection(self):
        """Should remove null byte injection attempts."""
        filename = "safe.mp3\x00.exe"
        result = sanitize_filename(filename)
        
        assert "\x00" not in result
        assert ".exe" not in result or result.endswith(".mp3")
    
    def test_homoglyph_attacks(self):
        """Should handle homoglyph attempts in filenames."""
        # Cyrillic 'a' that looks like Latin 'a'
        filename = "f\u0430ile.mp3"  # а is Cyrillic
        result = sanitize_filename(filename)
        
        # Should be sanitized or preserved safely
        assert isinstance(result, str)
    
    def test_very_large_file_size(self):
        """Should handle very large file sizes."""
        # 100 GB
        with pytest.raises(ValidationError):
            validate_file_size(100 * 1024 * 1024 * 1024)
    
    def test_unicode_normalization(self):
        """Should handle unicode normalization."""
        # Same visual character, different unicode representations
        filename1 = "caf\u00e9.mp3"  # é as single character
        filename2 = "cafe\u0301.mp3"  # e + combining accent
        
        result1 = sanitize_filename(filename1)
        result2 = sanitize_filename(filename2)
        
        # Both should be valid
        assert result1.endswith(".mp3")
        assert result2.endswith(".mp3")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
