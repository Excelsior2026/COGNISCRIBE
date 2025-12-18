import os, shutil
from datetime import datetime, timedelta
from src.utils.settings import AUDIO_STORAGE_DIR, AUDIO_RETENTION_DAYS

def cleanup_old_audio():
    cutoff = datetime.utcnow() - timedelta(days=AUDIO_RETENTION_DAYS)

    for folder in os.listdir(AUDIO_STORAGE_DIR):
        try:
            date = datetime.strptime(folder, "%Y-%m-%d")
            if date < cutoff:
                shutil.rmtree(os.path.join(AUDIO_STORAGE_DIR, folder))
        except:
            continue
