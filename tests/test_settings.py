"""Unit tests for Pydantic settings module."""
import os
import pytest
from pydantic import ValidationError as PydanticValidationError
from src.utils.settings import CogniScribeSettings, get_settings


class TestCogniScribeSettings:
    """Test Pydantic settings validation and computed fields."""
    
    def test_default_settings(self):
        """Should load with all default values."""
        settings = CogniScribeSettings()
        
        # Audio storage
        assert settings.audio_retention_days == 7
        assert settings.max_file_size_mb == 1000
        assert settings.max_chunk_mb == 8
        
        # Security
        assert settings.phi_detection_enabled is True
        
        # Whisper
        assert settings.whisper_model == "base"
        assert settings.use_gpu is False
        
        # Ollama
        assert settings.ollama_host == "localhost"
        assert settings.ollama_port == "11434"
        assert settings.ollama_model == "llama3.1:8b"
        assert settings.ollama_timeout == 300
        
        # Logging
        assert settings.log_level == "INFO"
    
    def test_audio_retention_days_validation(self):
        """Should validate audio retention days range."""
        # Valid values
        CogniScribeSettings(audio_retention_days=1)
        CogniScribeSettings(audio_retention_days=365)
        CogniScribeSettings(audio_retention_days=30)
        
        # Invalid: too low
        with pytest.raises(PydanticValidationError) as exc_info:
            CogniScribeSettings(audio_retention_days=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()
        
        # Invalid: too high
        with pytest.raises(PydanticValidationError) as exc_info:
            CogniScribeSettings(audio_retention_days=366)
        assert "less than or equal to 365" in str(exc_info.value).lower()
    
    def test_max_file_size_validation(self):
        """Should validate max file size range."""
        # Valid values
        CogniScribeSettings(max_file_size_mb=1)
        CogniScribeSettings(max_file_size_mb=10000)
        CogniScribeSettings(max_file_size_mb=500)
        
        # Invalid: too low
        with pytest.raises(PydanticValidationError) as exc_info:
            CogniScribeSettings(max_file_size_mb=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()
        
        # Invalid: too high
        with pytest.raises(PydanticValidationError) as exc_info:
            CogniScribeSettings(max_file_size_mb=10001)
        assert "less than or equal to 10000" in str(exc_info.value).lower()
    
    def test_max_chunk_mb_validation(self):
        """Should validate max chunk size range."""
        # Valid
        CogniScribeSettings(max_chunk_mb=8)
        
        # Invalid: too low
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(max_chunk_mb=0)
        
        # Invalid: too high
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(max_chunk_mb=101)
    
    def test_whisper_model_validation(self):
        """Should validate Whisper model enum."""
        # Valid models
        for model in ["tiny", "base", "small", "medium", "large-v3"]:
            settings = CogniScribeSettings(whisper_model=model)
            assert settings.whisper_model == model
        
        # Invalid model
        with pytest.raises(PydanticValidationError) as exc_info:
            CogniScribeSettings(whisper_model="invalid-model")
        assert "input should be" in str(exc_info.value).lower()
    
    def test_log_level_validation(self):
        """Should validate log level enum."""
        # Valid levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = CogniScribeSettings(log_level=level)
            assert settings.log_level == level
        
        # Case insensitive
        settings = CogniScribeSettings(log_level="info")
        assert settings.log_level == "INFO"
        
        # Invalid level
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(log_level="INVALID")
    
    def test_ollama_timeout_validation(self):
        """Should validate Ollama timeout range."""
        # Valid values
        CogniScribeSettings(ollama_timeout=30)
        CogniScribeSettings(ollama_timeout=3600)
        CogniScribeSettings(ollama_timeout=300)
        
        # Invalid: too low
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(ollama_timeout=29)
        
        # Invalid: too high
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(ollama_timeout=3601)
    
    def test_ollama_host_validation(self):
        """Should validate Ollama host is not empty."""
        # Valid
        CogniScribeSettings(ollama_host="localhost")
        CogniScribeSettings(ollama_host="http://ollama:11434")
        
        # Invalid: empty
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(ollama_host="")
        
        # Invalid: whitespace only
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(ollama_host="   ")
    
    def test_ollama_model_validation(self):
        """Should validate Ollama model is not empty."""
        # Valid
        CogniScribeSettings(ollama_model="llama3.1:8b")
        CogniScribeSettings(ollama_model="mistral:7b")
        
        # Invalid: empty
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(ollama_model="")
    
    def test_allowed_audio_formats_normalization(self):
        """Should normalize audio formats to start with dot."""
        settings = CogniScribeSettings(
            allowed_audio_formats=["mp3", ".wav", "flac"]
        )
        
        # All should have leading dot
        assert all(fmt.startswith(".") for fmt in settings.allowed_audio_formats)
        assert ".mp3" in settings.allowed_audio_formats
        assert ".wav" in settings.allowed_audio_formats
        assert ".flac" in settings.allowed_audio_formats
    
    def test_device_computed_field(self):
        """Should compute device from use_gpu."""
        # GPU enabled
        settings = CogniScribeSettings(use_gpu=True)
        assert settings.device == "cuda"
        
        # GPU disabled
        settings = CogniScribeSettings(use_gpu=False)
        assert settings.device == "cpu"
    
    def test_compute_type_computed_field(self):
        """Should compute compute_type from device."""
        # CUDA device
        settings = CogniScribeSettings(use_gpu=True)
        assert settings.compute_type == "float16"
        
        # CPU device
        settings = CogniScribeSettings(use_gpu=False)
        assert settings.compute_type == "int8"
    
    def test_ollama_url_computed_field(self):
        """Should construct Ollama URL from host and port."""
        # Basic hostname
        settings = CogniScribeSettings(
            ollama_host="localhost",
            ollama_port="11434"
        )
        assert settings.ollama_url == "http://localhost:11434/api/generate"
        
        # Full URL in host
        settings = CogniScribeSettings(
            ollama_host="http://ollama:11434",
            ollama_port="11434"
        )
        assert settings.ollama_url == "http://ollama:11434/api/generate"
        
        # HTTPS URL
        settings = CogniScribeSettings(
            ollama_host="https://api.example.com",
            ollama_port="11434"
        )
        assert settings.ollama_url == "https://api.example.com/api/generate"
    
    def test_cors_origins_list_computed_field(self):
        """Should parse CORS origins from comma-separated string."""
        settings = CogniScribeSettings(
            cors_allow_origins="http://localhost,http://127.0.0.1,http://localhost:5173"
        )
        
        origins = settings.cors_origins_list
        assert len(origins) == 3
        assert "http://localhost" in origins
        assert "http://127.0.0.1" in origins
        assert "http://localhost:5173" in origins
    
    def test_cors_origins_with_whitespace(self):
        """Should handle whitespace in CORS origins."""
        settings = CogniScribeSettings(
            cors_allow_origins="http://localhost , http://127.0.0.1 ,  http://localhost:5173"
        )
        
        origins = settings.cors_origins_list
        assert len(origins) == 3
        # Whitespace should be stripped
        assert all(not o.startswith(" ") and not o.endswith(" ") for o in origins)
    
    def test_max_chunk_bytes_computed_field(self):
        """Should convert max chunk MB to bytes."""
        settings = CogniScribeSettings(max_chunk_mb=8)
        assert settings.max_chunk_bytes == 8 * 1024 * 1024
        
        settings = CogniScribeSettings(max_chunk_mb=16)
        assert settings.max_chunk_bytes == 16 * 1024 * 1024
    
    def test_base_data_dir_default(self):
        """Should provide platform-specific base data dir."""
        settings = CogniScribeSettings()
        base_dir = settings.base_data_dir
        
        # Should be a valid path
        assert isinstance(base_dir, str)
        assert len(base_dir) > 0
        
        # Should contain cogniscribe in path
        assert "cogniscribe" in base_dir.lower()
    
    def test_base_data_dir_override(self):
        """Should use COGNISCRIBE_DATA_DIR override."""
        settings = CogniScribeSettings(cogniscribe_data_dir="/custom/path")
        assert "/custom/path" in settings.base_data_dir
    
    def test_resolved_directories(self):
        """Should resolve audio storage directories."""
        settings = CogniScribeSettings()
        
        # Should have valid paths
        assert isinstance(settings.resolved_audio_storage_dir, str)
        assert isinstance(settings.resolved_temp_audio_dir, str)
        
        # Should contain expected directory names
        assert "audio_storage" in settings.resolved_audio_storage_dir
        assert "temp_processed" in settings.resolved_temp_audio_dir
    
    def test_directory_overrides(self):
        """Should allow overriding specific directories."""
        settings = CogniScribeSettings(
            audio_storage_dir="/custom/audio",
            temp_audio_dir="/custom/temp"
        )
        
        assert "/custom/audio" in settings.resolved_audio_storage_dir
        assert "/custom/temp" in settings.resolved_temp_audio_dir
    
    def test_env_file_loading(self, tmp_path, monkeypatch):
        """Should load settings from .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "WHISPER_MODEL=small\n"
            "MAX_FILE_SIZE_MB=500\n"
            "LOG_LEVEL=DEBUG\n"
        )
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        settings = CogniScribeSettings()
        assert settings.whisper_model == "small"
        assert settings.max_file_size_mb == 500
        assert settings.log_level == "DEBUG"
    
    def test_singleton_get_settings(self):
        """Should return singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2


class TestBackwardCompatibility:
    """Test backward compatibility with module-level variables."""
    
    def test_module_level_imports(self):
        """Should export settings as module-level variables."""
        from src.utils.settings import (
            AUDIO_RETENTION_DAYS,
            AUDIO_STORAGE_DIR,
            TEMP_AUDIO_DIR,
            MAX_FILE_SIZE_MB,
            MAX_CHUNK_MB,
            MAX_CHUNK_BYTES,
            ALLOWED_AUDIO_FORMATS,
            PHI_DETECTION_ENABLED,
            WHISPER_MODEL,
            USE_GPU,
            DEVICE,
            COMPUTE_TYPE,
            OLLAMA_HOST,
            OLLAMA_PORT,
            OLLAMA_URL,
            OLLAMA_MODEL,
            OLLAMA_TIMEOUT,
            LOG_LEVEL,
            CORS_ALLOW_ORIGINS,
            API_TITLE,
            API_VERSION,
        )
        
        # All imports should work
        assert isinstance(AUDIO_RETENTION_DAYS, int)
        assert isinstance(AUDIO_STORAGE_DIR, str)
        assert isinstance(MAX_FILE_SIZE_MB, int)
        assert isinstance(WHISPER_MODEL, str)
        assert isinstance(DEVICE, str)
        assert isinstance(OLLAMA_URL, str)
        assert isinstance(LOG_LEVEL, str)
        assert isinstance(CORS_ALLOW_ORIGINS, list)
    
    def test_values_match_settings_instance(self):
        """Module-level variables should match settings instance."""
        from src.utils.settings import (
            WHISPER_MODEL,
            DEVICE,
            OLLAMA_URL,
            MAX_FILE_SIZE_MB,
        )
        
        settings = get_settings()
        
        assert WHISPER_MODEL == settings.whisper_model
        assert DEVICE == settings.device
        assert OLLAMA_URL == settings.ollama_url
        assert MAX_FILE_SIZE_MB == settings.max_file_size_mb


class TestSettingsEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_type_coercion(self):
        """Should fail on invalid type coercion."""
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(max_file_size_mb="not-a-number")
        
        with pytest.raises(PydanticValidationError):
            CogniScribeSettings(use_gpu="maybe")
    
    def test_extra_fields_ignored(self):
        """Should ignore unknown fields."""
        # Should not raise error
        settings = CogniScribeSettings(
            unknown_field="value",
            another_unknown=123
        )
        
        # Known fields should still work
        assert settings.whisper_model == "base"
    
    def test_empty_cors_origins(self):
        """Should handle empty CORS origins string."""
        settings = CogniScribeSettings(cors_allow_origins="")
        assert settings.cors_origins_list == []
    
    def test_cors_origins_with_empty_values(self):
        """Should filter out empty values in CORS origins."""
        settings = CogniScribeSettings(
            cors_allow_origins="http://localhost,,http://127.0.0.1, ,"
        )
        
        origins = settings.cors_origins_list
        # Should only have non-empty values
        assert len(origins) == 2
        assert "" not in origins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
