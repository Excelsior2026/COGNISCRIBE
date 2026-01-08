"""File deduplication utilities to prevent processing duplicate files."""
import os
import hashlib
from typing import Optional
from src.utils.file_utils import get_file_hash
from src.cache.redis_config import get_redis
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_file_hash_key(file_hash: str) -> str:
    """Get Redis key for file hash lookup."""
    return f"file_hash:{file_hash}"


def check_duplicate_file(file_path: str) -> Optional[dict]:
    """Check if a file with the same hash has been processed before.
    
    Args:
        file_path: Path to file to check
        
    Returns:
        Dictionary with task_id and result if duplicate found, None otherwise
    """
    try:
        # Calculate file hash
        file_hash = get_file_hash(file_path)
        
        # Check Redis cache
        try:
            redis_client = get_redis()
            cached_result = redis_client.get_cache(get_file_hash_key(file_hash))
            if cached_result:
                logger.info(f"Found duplicate file (hash: {file_hash[:16]}...)")
                return cached_result
        except Exception as e:
            logger.debug(f"Could not check Redis for duplicates: {str(e)}")
            # Continue without cache check
        
        return None
    except Exception as e:
        logger.warning(f"Failed to check for duplicate file: {str(e)}")
        return None


def cache_file_result(file_path: str, task_id: str, result: dict, ttl: int = 86400 * 7) -> bool:
    """Cache file processing result by hash.
    
    Args:
        file_path: Path to processed file
        task_id: Task ID that processed the file
        result: Processing result to cache
        ttl: Time to live in seconds (default 7 days)
        
    Returns:
        True if cached successfully, False otherwise
    """
    try:
        file_hash = get_file_hash(file_path)
        
        cache_data = {
            "task_id": task_id,
            "file_hash": file_hash,
            "result": result
        }
        
        try:
            redis_client = get_redis()
            redis_client.set_cache(get_file_hash_key(file_hash), cache_data, ttl=ttl)
            logger.debug(f"Cached result for file hash: {file_hash[:16]}...")
            return True
        except Exception as e:
            logger.debug(f"Could not cache file result: {str(e)}")
            return False
    except Exception as e:
        logger.warning(f"Failed to cache file result: {str(e)}")
        return False
