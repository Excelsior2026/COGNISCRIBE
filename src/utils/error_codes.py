"""Structured error codes for API responses."""
from enum import Enum
from typing import Optional
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """Enumeration of application error codes."""
    
    # File validation errors
    INVALID_FILE_FORMAT = "invalid_file_format"
    FILE_TOO_LARGE = "file_too_large"
    FILE_CORRUPTED = "file_corrupted"
    
    # Processing errors
    PREPROCESSING_FAILED = "preprocessing_failed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    SUMMARIZATION_FAILED = "summarization_failed"
    PIPELINE_TIMEOUT = "pipeline_timeout"
    
    # Service errors
    OLLAMA_UNAVAILABLE = "ollama_unavailable"
    OLLAMA_TIMEOUT = "ollama_timeout"
    WHISPER_MODEL_ERROR = "whisper_model_error"
    
    # Authentication/Authorization
    INVALID_API_KEY = "invalid_api_key"
    MISSING_API_KEY = "missing_api_key"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # General errors
    INTERNAL_ERROR = "internal_error"
    INVALID_PARAMETERS = "invalid_parameters"


class APIError(HTTPException):
    """Custom exception with structured error response."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code.value,
                "message": message,
                "details": self.details
            }
        )


# Convenience functions for common errors
def file_too_large_error(size_mb: float, max_mb: int) -> APIError:
    return APIError(
        error_code=ErrorCode.FILE_TOO_LARGE,
        message=f"File too large ({size_mb:.1f}MB). Maximum allowed: {max_mb}MB",
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        details={"file_size_mb": size_mb, "max_size_mb": max_mb}
    )


def invalid_file_format_error(extension: str, allowed: list) -> APIError:
    return APIError(
        error_code=ErrorCode.INVALID_FILE_FORMAT,
        message=f"Unsupported file format '{extension}'. Allowed: {', '.join(allowed)}",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"extension": extension, "allowed_formats": allowed}
    )


def rate_limit_error(retry_after: int) -> APIError:
    return APIError(
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        details={"retry_after_seconds": retry_after}
    )


def ollama_unavailable_error(url: str) -> APIError:
    return APIError(
        error_code=ErrorCode.OLLAMA_UNAVAILABLE,
        message=f"Cannot connect to Ollama service at {url}. Ensure Ollama is running.",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        details={"ollama_url": url}
    )


def invalid_api_key_error() -> APIError:
    return APIError(
        error_code=ErrorCode.INVALID_API_KEY,
        message="Invalid API key provided.",
        status_code=status.HTTP_401_UNAUTHORIZED
    )


def missing_api_key_error() -> APIError:
    return APIError(
        error_code=ErrorCode.MISSING_API_KEY,
        message="API key required. Include X-API-Key header.",
        status_code=status.HTTP_401_UNAUTHORIZED
    )
