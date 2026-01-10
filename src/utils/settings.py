import os
import sys
from typing import Literal, Optional


def _default_data_dir() -> str:
    override = os.environ.get("COGNISCRIBE_DATA_DIR")
    if override:
        return os.path.abspath(override)

    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "com.bageltech.cogniscribe")
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or home
        return os.path.join(base, "CogniScribe")
    return os.path.join(home, ".local", "share", "cogniscribe")


def _resolve_data_path(env_value: Optional[str], default_name: str, base_dir: str) -> str:
    if env_value:
        return os.path.abspath(env_value)
    return os.path.join(base_dir, default_name)

# Audio storage settings
_BASE_DATA_DIR = _default_data_dir()
AUDIO_RETENTION_DAYS = int(os.environ.get("AUDIO_RETENTION_DAYS", "7"))
AUDIO_STORAGE_DIR = _resolve_data_path(
    os.environ.get("AUDIO_STORAGE_DIR"), "audio_storage", _BASE_DATA_DIR
)
TEMP_AUDIO_DIR = _resolve_data_path(
    os.environ.get("TEMP_AUDIO_DIR"), "temp_processed", _BASE_DATA_DIR
)

# File upload limits
MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "1000"))
MAX_CHUNK_MB = int(os.environ.get("MAX_CHUNK_MB", "8"))
MAX_CHUNK_BYTES = MAX_CHUNK_MB * 1024 * 1024
ALLOWED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma", ".webm", ".mp4", ".mkv"]

# DeepFilterNet (optional offline enhancement)
DEEPFILTERNET_ENABLED = os.environ.get("DEEPFILTERNET_ENABLED", "false").lower() in ("true", "1", "yes")
DEEPFILTERNET_BIN = os.environ.get("DEEPFILTERNET_BIN", "deep-filter")
DEEPFILTERNET_MODEL = os.environ.get("DEEPFILTERNET_MODEL", "").strip()
DEEPFILTERNET_USE_POSTFILTER = os.environ.get("DEEPFILTERNET_USE_POSTFILTER", "true").lower() in ("true", "1", "yes")

# Whisper model settings
WHISPER_MODEL: Literal["tiny", "base", "small", "medium", "large-v3"] = os.environ.get(
    "WHISPER_MODEL", "base"
)
USE_GPU = os.environ.get("USE_GPU", "false").lower() in ("true", "1", "yes")
DEVICE = "cuda" if USE_GPU else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# Ollama settings
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# CORS
_cors_origins = os.environ.get(
    "CORS_ALLOW_ORIGINS",
    ",".join(
        [
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "tauri://localhost",
            "app://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
        ]
    ),
)
CORS_ALLOW_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = os.environ.get("CORS_ALLOW_CREDENTIALS", "false").lower() in (
    "true",
    "1",
    "yes",
)

# API settings
API_TITLE = "CogniScribe API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Audio transcription and summarization for medical/nursing students. "
    "Educational use only. Do not upload live clinical data or PHI. "
    "Not for diagnosis, treatment, or clinical decision-making."
)

# Reasoning Core (optional)
REASONING_CORE_ENABLED = os.environ.get("REASONING_CORE_ENABLED", "false").lower() in (
    "true",
    "1",
    "yes",
)
REASONING_CORE_DOMAIN = os.environ.get("REASONING_CORE_DOMAIN", "medical")
REASONING_CORE_USE_LLM = os.environ.get("REASONING_CORE_USE_LLM", "true").lower() in (
    "true",
    "1",
    "yes",
    "auto",
)
