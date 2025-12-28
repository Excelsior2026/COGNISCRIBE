"""Structured error handling for CliniScribe."""
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    # File upload errors
    FILE_TOO_LARGE = "file_too_large"
    INVALID_FILE_FORMAT = "invalid_file_format"
    INVALID_FILE_SIGNATURE = "invalid_file_signature"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    
    # Processing errors
    PREPROCESSING_FAILED = "preprocessing_failed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    SUMMARIZATION_FAILED = "summarization_failed"
    PIPELINE_FAILED = "pipeline_failed"
    
    # Service errors
    OLLAMA_UNAVAILABLE = "ollama_unavailable"
    OLLAMA_TIMEOUT = "ollama_timeout"
    WHISPER_MODEL_ERROR = "whisper_model_error"
    
    # Authentication/Authorization
    UNAUTHORIZED = "unauthorized"
    INVALID_API_KEY = "invalid_api_key"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # General errors
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"


class CliniScribeException(Exception):
    """Base exception for CliniScribe errors."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to API response format."""
        return {
            "success": False,
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details
        }


class FileValidationError(CliniScribeException):
    """Raised when file validation fails."""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.VALIDATION_ERROR):
        super().__init__(error_code, message, status_code=400)


class ProcessingError(CliniScribeException):
    """Raised when audio processing fails."""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.PIPELINE_FAILED):
        super().__init__(error_code, message, status_code=500)


class ServiceUnavailableError(CliniScribeException):
    """Raised when external service is unavailable."""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.OLLAMA_UNAVAILABLE):
        super().__init__(error_code, message, status_code=503)


class AuthenticationError(CliniScribeException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(ErrorCode.UNAUTHORIZED, message, status_code=401)


class RateLimitError(CliniScribeException):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(ErrorCode.RATE_LIMIT_EXCEEDED, message, status_code=429, details=details)
