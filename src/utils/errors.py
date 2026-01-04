"""Structured error codes and exception handling for COGNISCRIBE."""
from enum import Enum
from typing import Optional
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    # Validation errors
    INVALID_FILE_FORMAT = "invalid_file_format"
    FILE_TOO_LARGE = "file_too_large"
    INVALID_PARAMETERS = "invalid_parameters"
    PHI_DETECTED = "phi_detected"  # NEW: Protected Health Information detected
    
    # Processing errors
    PREPROCESSING_FAILED = "preprocessing_failed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    SUMMARIZATION_FAILED = "summarization_failed"
    
    # Service errors
    OLLAMA_UNAVAILABLE = "ollama_unavailable"
    OLLAMA_TIMEOUT = "ollama_timeout"
    WHISPER_MODEL_LOAD_FAILED = "whisper_model_load_failed"
    
    # Auth errors
    INVALID_API_KEY = "invalid_api_key"
    MISSING_API_KEY = "missing_api_key"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Generic
    INTERNAL_ERROR = "internal_error"
    UNKNOWN_ERROR = "unknown_error"


class CliniScribeException(Exception):
    """Base exception for COGNISCRIBE errors."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "error": self.error_code.value,
                "message": self.message,
                **self.details
            }
        )


class ValidationError(CliniScribeException):
    """Validation error."""
    def __init__(self, message: str, error_code: ErrorCode, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ProcessingError(CliniScribeException):
    """Processing error during pipeline execution."""
    def __init__(self, message: str, error_code: ErrorCode, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ServiceUnavailableError(CliniScribeException):
    """External service unavailable."""
    def __init__(self, message: str, error_code: ErrorCode, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class AuthenticationError(CliniScribeException):
    """Authentication error."""
    def __init__(self, message: str, error_code: ErrorCode, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class RateLimitError(CliniScribeException):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )
