"""API Key authentication middleware for CLINISCRIBE."""
import os
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from src.utils.errors import AuthenticationError, ErrorCode
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# API key configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
VALID_API_KEYS = set()

# Load API keys from environment
API_KEYS_ENV = os.getenv("CLINISCRIBE_API_KEYS", "")
if API_KEYS_ENV:
    VALID_API_KEYS = set(key.strip() for key in API_KEYS_ENV.split(",") if key.strip())
    logger.info(f"Loaded {len(VALID_API_KEYS)} API keys from environment")
else:
    # Generate a development key if none configured
    DEV_KEY = os.getenv("CLINISCRIBE_DEV_KEY")
    if not DEV_KEY:
        DEV_KEY = secrets.token_urlsafe(32)
        # Log that a key was generated but don't expose it in logs
        logger.warning(
            "No API keys configured. A development key has been generated.\n"
            "⚠️  SECURITY: Set CLINISCRIBE_API_KEYS environment variable for production.\n"
            "⚠️  For development, retrieve the generated key from the application startup output or set CLINISCRIBE_DEV_KEY."
        )
        # Print to stderr (not logs) so it's visible but not in log files
        import sys
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"DEVELOPMENT API KEY: {DEV_KEY}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
    VALID_API_KEYS.add(DEV_KEY)

# Authentication enabled/disabled
AUTH_ENABLED = os.getenv("CLINISCRIBE_AUTH_ENABLED", "true").lower() in ("true", "1", "yes")

if not AUTH_ENABLED:
    logger.warning("Authentication is DISABLED. This should only be used in development!")


def verify_api_key(api_key: Optional[str]) -> bool:
    """Verify if the provided API key is valid."""
    if not AUTH_ENABLED:
        return True
    
    if not api_key:
        return False
    
    return api_key in VALID_API_KEYS


async def authenticate_request(request: Request, api_key: Optional[str] = None) -> None:
    """Authenticate incoming request using API key.
    
    Args:
        request: The incoming request
        api_key: API key from header (injected by dependency)
        
    Raises:
        AuthenticationError: If authentication fails
    """
    if not AUTH_ENABLED:
        return
    
    # Check for API key in header
    if not api_key:
        api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        logger.warning(f"Missing API key for {request.url.path} from {request.client.host}")
        raise AuthenticationError(
            message="API key is required. Include X-API-Key header in your request.",
            error_code=ErrorCode.MISSING_API_KEY,
            details={"header": "X-API-Key"}
        )
    
    if not verify_api_key(api_key):
        logger.warning(f"Invalid API key attempt from {request.client.host}")
        raise AuthenticationError(
            message="Invalid API key provided.",
            error_code=ErrorCode.INVALID_API_KEY
        )
    
    # Successful authentication
    logger.debug(f"Authenticated request to {request.url.path}")


def generate_api_key() -> str:
    """Generate a new secure API key.
    
    Returns:
        A URL-safe random string suitable for use as an API key
    """
    return secrets.token_urlsafe(32)


def add_api_key(api_key: str) -> None:
    """Add an API key to the valid keys set.
    
    Args:
        api_key: The API key to add
    """
    VALID_API_KEYS.add(api_key)
    logger.info(f"Added new API key (total: {len(VALID_API_KEYS)})")


def remove_api_key(api_key: str) -> bool:
    """Remove an API key from the valid keys set.
    
    Args:
        api_key: The API key to remove
        
    Returns:
        True if the key was removed, False if it didn't exist
    """
    if api_key in VALID_API_KEYS:
        VALID_API_KEYS.remove(api_key)
        logger.info(f"Removed API key (remaining: {len(VALID_API_KEYS)})")
        return True
    return False
