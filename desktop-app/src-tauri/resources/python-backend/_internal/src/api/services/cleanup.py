import os
import shutil
from datetime import datetime, timedelta
from src.utils.settings import AUDIO_STORAGE_DIR, AUDIO_RETENTION_DAYS
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def cleanup_old_audio() -> None:
    """
    Remove audio files older than AUDIO_RETENTION_DAYS.
    Runs as a scheduled background task.
    """
    logger.info(f"Starting audio cleanup (retention: {AUDIO_RETENTION_DAYS} days)")
    
    if not os.path.exists(AUDIO_STORAGE_DIR):
        logger.warning(f"Audio storage directory does not exist: {AUDIO_STORAGE_DIR}")
        return
    
    cutoff = datetime.utcnow() - timedelta(days=AUDIO_RETENTION_DAYS)
    removed_count = 0
    error_count = 0
    
    try:
        for folder in os.listdir(AUDIO_STORAGE_DIR):
            folder_path = os.path.join(AUDIO_STORAGE_DIR, folder)
            
            # Skip non-directories
            if not os.path.isdir(folder_path):
                continue
            
            try:
                # Parse folder name as date (YYYY-MM-DD format)
                folder_date = datetime.strptime(folder, "%Y-%m-%d")
                
                if folder_date < cutoff:
                    logger.info(f"Removing old audio folder: {folder}")
                    shutil.rmtree(folder_path)
                    removed_count += 1
                    
            except ValueError:
                logger.warning(f"Skipping folder with invalid date format: {folder}")
                continue
            except Exception as e:
                logger.error(f"Failed to remove folder {folder}: {str(e)}")
                error_count += 1
                continue
        
        logger.info(f"Audio cleanup completed: {removed_count} folders removed, {error_count} errors")
        
    except Exception as e:
        logger.error(f"Audio cleanup failed: {str(e)}")
