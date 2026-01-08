"""File utility functions for CogniScribe."""
import os
import hashlib
import shutil
from typing import Optional, Tuple
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_file_hash(file_path: str, chunk_size: int = 8192) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read (for large files)
        
    Returns:
        Hexadecimal hash string
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate file hash: {str(e)}")
        raise


def check_disk_space(path: str, required_bytes: int) -> Tuple[bool, Optional[str]]:
    """Check if sufficient disk space is available.
    
    Args:
        path: Path to check disk space for
        required_bytes: Required bytes
        
    Returns:
        Tuple of (has_space, error_message)
    """
    try:
        stat = shutil.disk_usage(os.path.dirname(path) if os.path.isfile(path) else path)
        free_bytes = stat.free
        
        if free_bytes < required_bytes:
            required_mb = required_bytes / (1024 * 1024)
            free_mb = free_bytes / (1024 * 1024)
            error_msg = (
                f"Insufficient disk space. Required: {required_mb:.1f}MB, "
                f"Available: {free_mb:.1f}MB"
            )
            return False, error_msg
        
        return True, None
    except Exception as e:
        logger.warning(f"Could not check disk space: {str(e)}")
        # Don't fail if we can't check, but log warning
        return True, None


def safe_remove_file(file_path: str) -> bool:
    """Safely remove a file, handling errors gracefully.
    
    Args:
        file_path: Path to file to remove
        
    Returns:
        True if file was removed, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Removed file: {file_path}")
            return True
        return False
    except PermissionError:
        logger.warning(f"Permission denied removing file: {file_path}")
        return False
    except Exception as e:
        logger.warning(f"Failed to remove file {file_path}: {str(e)}")
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes, or None if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None
