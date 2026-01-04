"""Unit tests for error handling and exception classes."""

import pytest
from fastapi import HTTPException, status
from src.utils.errors import (
    ErrorCode,
    CliniScribeException,
    ValidationError,
    ProcessingError,
    ServiceUnavailableError,
    AuthenticationError,
    RateLimitError
)


class TestErrorCode:
    """Test ErrorCode enum."""
    
    def test_error_code_values(self):
        """Test error codes have correct string values."""
        assert ErrorCode.INVALID_FILE_FORMAT.value == "invalid_file_format"
        assert ErrorCode.FILE_TOO_LARGE.value == "file_too_large"
        assert ErrorCode.PHI_DETECTED.value == "phi_detected"
        assert ErrorCode.TRANSCRIPTION_FAILED.value == "transcription_failed"
        assert ErrorCode.OLLAMA_UNAVAILABLE.value == "ollama_unavailable"
    
    def test_error_code_string_comparison(self):
        """Test error codes can be compared to strings."""
        assert ErrorCode.INVALID_FILE_FORMAT == "invalid_file_format"
        assert ErrorCode.RATE_LIMIT_EXCEEDED == "rate_limit_exceeded"


class TestCliniScribeException:
    """Test base exception class."""
    
    def test_exception_basic_properties(self):
        """Test exception has correct properties."""
        exc = CliniScribeException(
            message="Test error",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 500
        assert exc.details == {}
    
    def test_exception_with_details(self):
        """Test exception preserves details."""
        details = {"filename": "test.mp3", "size_mb": 150}
        exc = CliniScribeException(
            message="File error",
            error_code=ErrorCode.FILE_TOO_LARGE,
            details=details
        )
        
        assert exc.details == details
        assert exc.details["filename"] == "test.mp3"
    
    def test_exception_to_http_exception(self):
        """Test conversion to FastAPI HTTPException."""
        exc = CliniScribeException(
            message="Test error",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details={"extra": "info"}
        )
        
        http_exc = exc.to_http_exception()
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 500
        assert http_exc.detail["error"] == "internal_error"
        assert http_exc.detail["message"] == "Test error"
        assert http_exc.detail["extra"] == "info"


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error_status_code(self):
        """Test ValidationError has 400 status code."""
        exc = ValidationError(
            message="Invalid input",
            error_code=ErrorCode.INVALID_PARAMETERS
        )
        
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.status_code == 400
    
    def test_validation_error_with_details(self):
        """Test ValidationError preserves validation details."""
        exc = ValidationError(
            message="File too large",
            error_code=ErrorCode.FILE_TOO_LARGE,
            details={"size_mb": 120, "max_mb": 100}
        )
        
        assert exc.details["size_mb"] == 120
        assert exc.details["max_mb"] == 100
    
    def test_validation_error_http_conversion(self):
        """Test ValidationError converts to HTTP 400."""
        exc = ValidationError(
            message="Invalid format",
            error_code=ErrorCode.INVALID_FILE_FORMAT,
            details={"extension": ".txt"}
        )
        
        http_exc = exc.to_http_exception()
        
        assert http_exc.status_code == 400
        assert http_exc.detail["error"] == "invalid_file_format"
        assert http_exc.detail["extension"] == ".txt"


class TestProcessingError:
    """Test ProcessingError exception."""
    
    def test_processing_error_status_code(self):
        """Test ProcessingError has 500 status code."""
        exc = ProcessingError(
            message="Transcription failed",
            error_code=ErrorCode.TRANSCRIPTION_FAILED
        )
        
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.status_code == 500
    
    def test_processing_error_with_stage_info(self):
        """Test ProcessingError can include pipeline stage info."""
        exc = ProcessingError(
            message="Preprocessing failed",
            error_code=ErrorCode.PREPROCESSING_FAILED,
            details={"stage": "audio_normalization", "error": "librosa error"}
        )
        
        assert exc.details["stage"] == "audio_normalization"
        assert exc.details["error"] == "librosa error"


class TestServiceUnavailableError:
    """Test ServiceUnavailableError exception."""
    
    def test_service_error_status_code(self):
        """Test ServiceUnavailableError has 503 status code."""
        exc = ServiceUnavailableError(
            message="Ollama unavailable",
            error_code=ErrorCode.OLLAMA_UNAVAILABLE
        )
        
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc.status_code == 503
    
    def test_service_error_with_retry_info(self):
        """Test ServiceUnavailableError can include retry information."""
        exc = ServiceUnavailableError(
            message="Service overloaded",
            error_code=ErrorCode.OLLAMA_UNAVAILABLE,
            details={"retry_after": 30, "service": "ollama"}
        )
        
        assert exc.details["retry_after"] == 30
        assert exc.details["service"] == "ollama"


class TestAuthenticationError:
    """Test AuthenticationError exception."""
    
    def test_auth_error_status_code(self):
        """Test AuthenticationError has 401 status code."""
        exc = AuthenticationError(
            message="Invalid API key",
            error_code=ErrorCode.INVALID_API_KEY
        )
        
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.status_code == 401
    
    def test_auth_error_http_conversion(self):
        """Test AuthenticationError converts to HTTP 401."""
        exc = AuthenticationError(
            message="Missing API key",
            error_code=ErrorCode.MISSING_API_KEY
        )
        
        http_exc = exc.to_http_exception()
        
        assert http_exc.status_code == 401
        assert http_exc.detail["error"] == "missing_api_key"


class TestRateLimitError:
    """Test RateLimitError exception."""
    
    def test_rate_limit_error_status_code(self):
        """Test RateLimitError has 429 status code."""
        exc = RateLimitError(
            message="Too many requests"
        )
        
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.status_code == 429
        assert exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
    
    def test_rate_limit_with_retry_after(self):
        """Test RateLimitError includes retry_after."""
        exc = RateLimitError(
            message="Rate limit exceeded",
            retry_after=60
        )
        
        assert exc.details["retry_after"] == 60
    
    def test_rate_limit_without_retry_after(self):
        """Test RateLimitError works without retry_after."""
        exc = RateLimitError(
            message="Rate limit exceeded"
        )
        
        assert exc.details == {}


class TestErrorPropagation:
    """Test error propagation through layers."""
    
    def test_exception_hierarchy(self):
        """Test all exceptions inherit from CliniScribeException."""
        assert issubclass(ValidationError, CliniScribeException)
        assert issubclass(ProcessingError, CliniScribeException)
        assert issubclass(ServiceUnavailableError, CliniScribeException)
        assert issubclass(AuthenticationError, CliniScribeException)
        assert issubclass(RateLimitError, CliniScribeException)
    
    def test_exception_catchable_as_base(self):
        """Test specific exceptions can be caught as base exception."""
        try:
            raise ValidationError(
                message="Test",
                error_code=ErrorCode.INVALID_PARAMETERS
            )
        except CliniScribeException as e:
            assert isinstance(e, ValidationError)
            assert isinstance(e, CliniScribeException)
    
    def test_multiple_exception_types(self):
        """Test catching multiple exception types."""
        exceptions = [
            ValidationError("Validation", ErrorCode.INVALID_PARAMETERS),
            ProcessingError("Processing", ErrorCode.TRANSCRIPTION_FAILED),
            ServiceUnavailableError("Service", ErrorCode.OLLAMA_UNAVAILABLE)
        ]
        
        for exc in exceptions:
            assert isinstance(exc, CliniScribeException)
            assert hasattr(exc, 'message')
            assert hasattr(exc, 'error_code')
            assert hasattr(exc, 'status_code')
            assert hasattr(exc, 'details')
