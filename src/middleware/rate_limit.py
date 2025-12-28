"""Rate limiting middleware."""
import time
from typing import Dict, Tuple
from collections import defaultdict, deque
from fastapi import Request
from src.utils.logger import setup_logger
from src.utils.error_codes import rate_limit_error

logger = setup_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 10, requests_per_hour: int = 100):
        """
        Args:
            requests_per_minute: Maximum requests per minute per client
            requests_per_hour: Maximum requests per hour per client
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Track requests per client (IP or API key)
        # Format: {client_id: deque([timestamp1, timestamp2, ...])}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=requests_per_hour))
        
        # Track when to clear old data
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
    
    def _cleanup_old_entries(self):
        """Remove stale client data to prevent memory leaks."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove clients with no requests in the last hour
        cutoff = now - 3600
        stale_clients = [
            client_id
            for client_id, history in self.request_history.items()
            if not history or history[-1] < cutoff
        ]
        
        for client_id in stale_clients:
            del self.request_history[client_id]
        
        self.last_cleanup = now
        logger.debug(f"Rate limiter cleanup: removed {len(stale_clients)} stale clients")
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """Check if request is allowed for client.
        
        Args:
            client_id: Identifier for the client (IP or API key)
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        history = self.request_history[client_id]
        
        # Remove requests older than 1 hour
        cutoff_hour = now - 3600
        while history and history[0] < cutoff_hour:
            history.popleft()
        
        # Check hourly limit
        if len(history) >= self.requests_per_hour:
            oldest_request = history[0]
            retry_after = int(oldest_request + 3600 - now) + 1
            logger.warning(f"Rate limit exceeded (hourly) for client: {client_id}")
            return False, retry_after
        
        # Check per-minute limit
        cutoff_minute = now - 60
        recent_requests = sum(1 for ts in history if ts > cutoff_minute)
        
        if recent_requests >= self.requests_per_minute:
            # Find oldest request in the last minute
            oldest_in_minute = min(ts for ts in history if ts > cutoff_minute)
            retry_after = int(oldest_in_minute + 60 - now) + 1
            logger.warning(f"Rate limit exceeded (per-minute) for client: {client_id}")
            return False, retry_after
        
        # Request allowed
        history.append(now)
        
        # Periodic cleanup
        self._cleanup_old_entries()
        
        return True, 0
    
    def get_client_stats(self, client_id: str) -> dict:
        """Get rate limit statistics for a client.
        
        Args:
            client_id: Identifier for the client
            
        Returns:
            Dictionary with current usage statistics
        """
        now = time.time()
        history = self.request_history[client_id]
        
        # Count requests in different time windows
        last_minute = sum(1 for ts in history if now - ts < 60)
        last_hour = len(history)
        
        return {
            "requests_last_minute": last_minute,
            "requests_last_hour": last_hour,
            "limit_per_minute": self.requests_per_minute,
            "limit_per_hour": self.requests_per_hour,
            "remaining_minute": max(0, self.requests_per_minute - last_minute),
            "remaining_hour": max(0, self.requests_per_hour - last_hour),
        }


# Global rate limiter instance
# Load limits from environment
import os
REQUESTS_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "10"))
REQUESTS_PER_HOUR = int(os.environ.get("RATE_LIMIT_PER_HOUR", "100"))

rate_limiter = RateLimiter(
    requests_per_minute=REQUESTS_PER_MINUTE,
    requests_per_hour=REQUESTS_PER_HOUR
)


async def check_rate_limit(request: Request, client_id: str = None) -> None:
    """Check rate limit for incoming request.
    
    Args:
        request: FastAPI request object
        client_id: Optional client identifier (uses IP if not provided)
        
    Raises:
        APIError: If rate limit is exceeded
    """
    # Check if rate limiting is disabled (for development)
    if os.environ.get("DISABLE_RATE_LIMIT", "false").lower() in ("true", "1", "yes"):
        return
    
    # Get client identifier (API key or IP)
    if not client_id:
        # Try to get API key first
        client_id = request.headers.get("X-API-Key")
        
        # Fall back to IP address
        if not client_id:
            # Get real IP (handle proxies)
            client_id = (
                request.headers.get("X-Forwarded-For", "")
                .split(",")[0]
                .strip()
            )
            if not client_id:
                client_id = request.client.host if request.client else "unknown"
    
    # Check rate limit
    allowed, retry_after = rate_limiter.is_allowed(client_id)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_id}, retry after {retry_after}s")
        raise rate_limit_error(retry_after)
    
    # Add rate limit info to response headers (done in middleware)
    stats = rate_limiter.get_client_stats(client_id)
    request.state.rate_limit_stats = stats
