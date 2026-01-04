"""Application settings using Pydantic Settings for validation.

Provides type-safe, validated configuration from environment variables.
Fails fast on invalid configuration with helpful error messages.
"""

import os
import sys
from typing import Literal, Optional, List
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CogniScribeSettings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ======= Audio Storage Settings =======
    
    cogniscribe_data_dir: Optional[str] = Field(
        default=None,
        description="Base directory for all data storage"
    )
    
    audio_retention_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Number of days to retain audio files"
    )
    
    audio_storage_dir: Optional[str] = Field(
        default=None,
        description="Directory for uploaded audio files"
    )
    
    temp_audio_dir: Optional[str] = Field(
        default=None,
        description="Directory for temporary processed audio"
    )
    
    # ======= File Upload Limits =======
    
    max_file_size_mb: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum file upload size in MB"
    )
    
    max_chunk_mb: int = Field(
        default=8,
        ge=1,
        le=100,
        description="Maximum chunk size for processing"
    )
    
    allowed_audio_formats: List[str] = Field(
        default=[".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma", ".webm", ".mp4", ".mkv"],
        description="Allowed audio file extensions"
    )
    
    # ======= Security =======
    
    phi_detection_enabled: bool = Field(
        default=True,
        description="Enable PHI detection to prevent uploading protected health information"
    )
    
    # ======= DeepFilterNet Enhancement =======
    
    deepfilternet_enabled: bool = Field(
        default=False,
        description="Enable DeepFilterNet audio enhancement (requires installation)"
    )
    
    deepfilternet_bin: str = Field(
        default="deep-filter",
        description="Path to DeepFilterNet binary"
    )
    
    deepfilternet_model: str = Field(
        default="",
        description="Path to DeepFilterNet model"
    )
    
    deepfilternet_use_postfilter: bool = Field(
        default=True,
        description="Use postfilter for DeepFilterNet"
    )
    
    # ======= Whisper Settings =======
    
    whisper_model: Literal["tiny", "base", "small", "medium", "large-v3"] = Field(
        default="base",
        description="Whisper model size (tiny, base, small, medium, large-v3)"
    )
    
    use_gpu: bool = Field(
        default=False,
        description="Use GPU for Whisper transcription (requires CUDA)"
    )
    
    @computed_field
    @property
    def device(self) -> Literal["cuda", "cpu"]:
        """Compute device based on use_gpu setting."""
        return "cuda" if self.use_gpu else "cpu"
    
    @computed_field
    @property
    def compute_type(self) -> Literal["float16", "int8"]:
        """Compute type based on device."""
        return "float16" if self.device == "cuda" else "int8"
    
    # ======= Ollama Settings =======
    
    ollama_host: str = Field(
        default="localhost",
        description="Ollama host (hostname or URL)"
    )
    
    ollama_port: str = Field(
        default="11434",
        description="Ollama port"
    )
    
    ollama_model: str = Field(
        default="llama3.1:8b",
        description="Ollama model name"
    )
    
    ollama_timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Ollama request timeout in seconds"
    )
    
    @computed_field
    @property
    def ollama_url(self) -> str:
        """Construct Ollama API URL from host and port."""
        # Handle if ollama_host is already a full URL
        if self.ollama_host.startswith("http://") or self.ollama_host.startswith("https://"):
            base = self.ollama_host.rstrip("/")
        else:
            base = f"http://{self.ollama_host}:{self.ollama_port}"
        return f"{base}/api/generate"
    
    # ======= Logging =======
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # ======= CORS =======
    
    cors_allow_origins: str = Field(
        default="http://localhost,http://127.0.0.1,http://localhost:5173,http://127.0.0.1:5173,tauri://localhost,app://localhost,http://tauri.localhost,https://tauri.localhost",
        description="Comma-separated list of allowed CORS origins"
    )
    
    cors_allow_credentials: bool = Field(
        default=False,
        description="Allow credentials in CORS requests"
    )
    
    @computed_field
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
    
    # ======= API Metadata =======
    
    api_title: str = Field(
        default="CogniScribe API",
        description="API title for documentation"
    )
    
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    
    api_description: str = Field(
        default=(
            "Audio transcription and summarization for medical/nursing students. "
            "Educational use only. Do not upload live clinical data or PHI. "
            "Not for diagnosis, treatment, or clinical decision-making."
        ),
        description="API description for documentation"
    )
    
    # ======= Computed Fields =======
    
    @computed_field
    @property
    def base_data_dir(self) -> str:
        """Get base data directory with platform-specific defaults."""
        if self.cogniscribe_data_dir:
            return os.path.abspath(self.cogniscribe_data_dir)
        
        home = os.path.expanduser("~")
        if sys.platform == "darwin":
            return os.path.join(home, "Library", "Application Support", "com.bageltech.cogniscribe")
        if os.name == "nt":
            base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or home
            return os.path.join(base, "CogniScribe")
        return os.path.join(home, ".local", "share", "cogniscribe")
    
    @computed_field
    @property
    def resolved_audio_storage_dir(self) -> str:
        """Resolve audio storage directory path."""
        if self.audio_storage_dir:
            return os.path.abspath(self.audio_storage_dir)
        return os.path.join(self.base_data_dir, "audio_storage")
    
    @computed_field
    @property
    def resolved_temp_audio_dir(self) -> str:
        """Resolve temp audio directory path."""
        if self.temp_audio_dir:
            return os.path.abspath(self.temp_audio_dir)
        return os.path.join(self.base_data_dir, "temp_processed")
    
    @computed_field
    @property
    def max_chunk_bytes(self) -> int:
        """Convert max chunk MB to bytes."""
        return self.max_chunk_mb * 1024 * 1024
    
    # ======= Validators =======
    
    @field_validator("allowed_audio_formats")
    @classmethod
    def validate_audio_formats(cls, v: List[str]) -> List[str]:
        """Ensure all formats start with a dot."""
        return [fmt if fmt.startswith(".") else f".{fmt}" for fmt in v]
    
    @field_validator("ollama_host")
    @classmethod
    def validate_ollama_host(cls, v: str) -> str:
        """Validate Ollama host format."""
        if not v or v.isspace():
            raise ValueError("ollama_host cannot be empty")
        return v.strip()
    
    @field_validator("ollama_model")
    @classmethod
    def validate_ollama_model(cls, v: str) -> str:
        """Validate Ollama model name."""
        if not v or v.isspace():
            raise ValueError("ollama_model cannot be empty")
        return v.strip()


# ======= Singleton Instance =======

_settings: Optional[CogniScribeSettings] = None


def get_settings() -> CogniScribeSettings:
    """Get singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = CogniScribeSettings()
    return _settings


# ======= Backward Compatibility =======
# Export settings as module-level variables for existing code

_s = get_settings()

# Audio storage
AUDIO_RETENTION_DAYS = _s.audio_retention_days
AUDIO_STORAGE_DIR = _s.resolved_audio_storage_dir
TEMP_AUDIO_DIR = _s.resolved_temp_audio_dir

# File limits
MAX_FILE_SIZE_MB = _s.max_file_size_mb
MAX_CHUNK_MB = _s.max_chunk_mb
MAX_CHUNK_BYTES = _s.max_chunk_bytes
ALLOWED_AUDIO_FORMATS = _s.allowed_audio_formats

# Security
PHI_DETECTION_ENABLED = _s.phi_detection_enabled

# DeepFilterNet
DEEPFILTERNET_ENABLED = _s.deepfilternet_enabled
DEEPFILTERNET_BIN = _s.deepfilternet_bin
DEEPFILTERNET_MODEL = _s.deepfilternet_model
DEEPFILTERNET_USE_POSTFILTER = _s.deepfilternet_use_postfilter

# Whisper
WHISPER_MODEL = _s.whisper_model
USE_GPU = _s.use_gpu
DEVICE = _s.device
COMPUTE_TYPE = _s.compute_type

# Ollama
OLLAMA_HOST = _s.ollama_host
OLLAMA_PORT = _s.ollama_port
OLLAMA_URL = _s.ollama_url
OLLAMA_MODEL = _s.ollama_model
OLLAMA_TIMEOUT = _s.ollama_timeout

# Logging
LOG_LEVEL = _s.log_level

# CORS
CORS_ALLOW_ORIGINS = _s.cors_origins_list
CORS_ALLOW_CREDENTIALS = _s.cors_allow_credentials

# API metadata
API_TITLE = _s.api_title
API_VERSION = _s.api_version
API_DESCRIPTION = _s.api_description
