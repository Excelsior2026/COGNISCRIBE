"""Request ID tracking for better debugging and logging."""
import uuid
from contextvars import ContextVar
from typing import Optional
from fastapi import Request
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Context variable for request ID
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Set request ID in context."""
    _request_id.set(request_id)


def generate_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


def get_or_create_request_id(request: Request) -> str:
    """Get request ID from header or generate new one.
    
    Checks for X-Request-ID header, or generates a new ID.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    # Check for existing request ID in header
    request_id = request.headers.get("X-Request-ID")
    
    if not request_id:
        request_id = generate_request_id()
    
    set_request_id(request_id)
    return request_id
