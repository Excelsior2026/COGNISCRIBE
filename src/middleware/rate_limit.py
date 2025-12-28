"""Rate limiting middleware for CLINISCRIBE API."""
import time
import os
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request
from src.utils.errors import RateLimitError
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Rate limit configuration
RATE_LIMIT_ENABLED = os.getenv("CLINISCRIBE_RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
RATE_LIMIT_REQUESTS = int(os.getenv("CLINISCRIBE_RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("CLINISCRIBE_RATE_LIMIT_WINDOW", "60"))  # seconds

if not RATE_LIMIT_ENABLED:
    logger.warning("Rate limiting is DISABLED. Enable for production use.")

# In-memory storage for rate limits
# Format: {client_id: [(timestamp, request_count), ...]}
rate_limit_store: Dict[str, list] = defaultdict(list)


def get_client_identifier(request: Request) -> str:
    """Get unique identifier for the client.
    
    Args:
        request: The incoming request
        
    Returns:
        Client identifier (IP address or API key)
    """
    # Prefer API key if available
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key[:8]}"  # Use first 8 chars for privacy
    
    # Fall back to IP address
    client_host = request.client.host if request.client else "unknown"
    
    # Check for forwarded IP (behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_host = forwarded_for.split(",")[0].strip()
    
    return f"ip:{client_host}"


def check_rate_limit(client_id: str) -> Tuple[bool, int, int]:
    """Check if client has exceeded rate limit.
    
    Args:
        client_id: Unique client identifier
        
    Returns:
        Tuple of (is_allowed, remaining_requests, retry_after_seconds)
    """
    if not RATE_LIMIT_ENABLED:
        return True, RATE_LIMIT_REQUESTS, 0
    
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    # Get client's request history
    requests = rate_limit_store[client_id]
    
    # Remove expired entries
    requests[:] = [req_time for req_time in requests if req_time > window_start]
    
    # Check if limit exceeded
    request_count = len(requests)
    remaining = max(0, RATE_LIMIT_REQUESTS - request_count)
    
    if request_count >= RATE_LIMIT_REQUESTS:
        # Calculate when the oldest request will expire
        oldest_request = min(requests)
        retry_after = int(oldest_request + RATE_LIMIT_WINDOW - current_time) + 1
        return False, 0, retry_after
    
    # Add current request
    requests.append(current_time)
    
    return True, remaining - 1, 0


async def rate_limit_middleware(request: Request) -> None:
    """Rate limiting middleware for API requests.
    
    Args:
        request: The incoming request
        
    Raises:
        RateLimitError: If rate limit is exceeded
    """
    if not RATE_LIMIT_ENABLED:
        return
    
    # Skip rate limiting for health check endpoint
    if request.url.path in ["/health", "/api/health"]:
        return
    
    client_id = get_client_identifier(request)
    is_allowed, remaining, retry_after = check_rate_limit(client_id)
    
    # Add rate limit headers to response (will be added by middleware)
    request.state.rate_limit_limit = RATE_LIMIT_REQUESTS
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = int(time.time()) + RATE_LIMIT_WINDOW
    
    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded for {client_id}: "
            f"{RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s"
        )
        raise RateLimitError(
            message=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
            retry_after=retry_after
        )
    
    logger.debug(f"Rate limit check passed for {client_id}: {remaining} remaining")


def cleanup_old_entries() -> int:
    """Clean up old rate limit entries to prevent memory bloat.
    
    Returns:
        Number of entries cleaned up
    """
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    cleaned = 0
    for client_id in list(rate_limit_store.keys()):
        requests = rate_limit_store[client_id]
        original_count = len(requests)
        
        # Remove expired entries
        requests[:] = [req_time for req_time in requests if req_time > window_start]
        
        cleaned += original_count - len(requests)
        
        # Remove client entry if no recent requests
        if not requests:
            del rate_limit_store[client_id]
    
    return cleaned


def get_rate_limit_stats() -> dict:
    """Get current rate limit statistics.
    
    Returns:
        Dictionary with rate limit statistics
    """
    return {
        "enabled": RATE_LIMIT_ENABLED,
        "limit": RATE_LIMIT_REQUESTS,
        "window_seconds": RATE_LIMIT_WINDOW,
        "active_clients": len(rate_limit_store),
        "total_tracked_requests": sum(len(requests) for requests in rate_limit_store.values())
    }
