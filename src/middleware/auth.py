"""API key authentication middleware."""
import secrets
import hashlib
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader
from src.utils.logger import setup_logger
from src.utils.error_codes import invalid_api_key_error, missing_api_key_error

logger = setup_logger(__name__)

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyManager:
    """Manages API key validation and storage."""
    
    def __init__(self):
        # In production, load from database or secure storage
        # For now, load from environment variable
        import os
        self.valid_keys = set()
        
        # Load API keys from environment (comma-separated)
        keys_str = os.environ.get("API_KEYS", "")
        if keys_str:
            self.valid_keys = set(k.strip() for k in keys_str.split(",") if k.strip())
        
        # If no keys configured, generate a default one for development
        if not self.valid_keys:
            default_key = os.environ.get("DEFAULT_API_KEY", "dev-key-cliniscribe-2025")
            self.valid_keys.add(default_key)
            logger.warning(
                f"No API_KEYS configured. Using default development key: {default_key}"
            )
    
    def validate_key(self, api_key: str) -> bool:
        """Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not api_key:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return any(
            secrets.compare_digest(api_key, valid_key) 
            for valid_key in self.valid_keys
        )
    
    @staticmethod
    def generate_key(prefix: str = "cs") -> str:
        """Generate a new API key.
        
        Args:
            prefix: Prefix for the key (default: 'cs' for CogniScribe)
            
        Returns:
            A new API key
        """
        # Generate 32 random bytes, convert to hex
        random_bytes = secrets.token_bytes(32)
        key_hash = hashlib.sha256(random_bytes).hexdigest()[:32]
        return f"{prefix}_{key_hash}"


# Global instance
api_key_manager = APIKeyManager()


async def verify_api_key(request: Request, api_key: Optional[str] = None) -> str:
    """Verify API key from request headers.
    
    Args:
        request: The FastAPI request object
        api_key: Optional API key from header
        
    Returns:
        The validated API key
        
    Raises:
        APIError: If API key is missing or invalid
    """
    # Check if authentication is disabled (for development)
    import os
    if os.environ.get("DISABLE_AUTH", "false").lower() in ("true", "1", "yes"):
        logger.warning("Authentication is DISABLED - not recommended for production!")
        return "auth_disabled"
    
    # Get API key from header
    if not api_key:
        api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        logger.warning(f"Missing API key for request: {request.url.path}")
        raise missing_api_key_error()
    
    # Validate key
    if not api_key_manager.validate_key(api_key):
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise invalid_api_key_error()
    
    logger.debug(f"API key validated for request: {request.url.path}")
    return api_key


def require_api_key(func):
    """Decorator to require API key authentication.
    
    Usage:
        @router.get("/protected")
        @require_api_key
        async def protected_endpoint(request: Request):
            ...
    """
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the request object in args or kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if not request:
            request = kwargs.get('request')
        
        if not request:
            raise HTTPException(status_code=500, detail="Request object not found")
        
        # Verify API key
        await verify_api_key(request)
        
        # Call original function
        return await func(*args, **kwargs)
    
    return wrapper
