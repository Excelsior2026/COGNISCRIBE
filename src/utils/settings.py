import os

AUDIO_RETENTION_DAYS = int(os.environ.get("AUDIO_RETENTION_DAYS", 7))
AUDIO_STORAGE_DIR = os.environ.get("AUDIO_STORAGE_DIR", "audio.tmp")
