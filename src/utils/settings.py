import os
from typing import Literal

# Audio storage settings
AUDIO_RETENTION_DAYS = int(os.environ.get("AUDIO_RETENTION_DAYS", "7"))
AUDIO_STORAGE_DIR = os.environ.get("AUDIO_STORAGE_DIR", "audio_storage")
TEMP_AUDIO_DIR = os.environ.get("TEMP_AUDIO_DIR", "temp_processed")

# File upload limits
MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "1000"))
ALLOWED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma"]

# Whisper model settings
WHISPER_MODEL: Literal["tiny", "base", "small", "medium", "large-v3"] = os.environ.get(
    "WHISPER_MODEL", "base"
)
USE_GPU = os.environ.get("USE_GPU", "false").lower() in ("true", "1", "yes")
DEVICE = "cuda" if USE_GPU else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# Ollama settings
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11436")
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# API settings
API_TITLE = "CliniScribe API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Audio transcription and summarization for medical/nursing students"
