"""Input validation and sanitization for CLINISCRIBE."""
import os
import re
import magic
from typing import Optional
from fastapi import UploadFile
from src.utils.settings import MAX_FILE_SIZE_MB, ALLOWED_AUDIO_FORMATS
from src.utils.errors import ValidationError, ErrorCode
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# MIME type mappings for audio files
AUDIO_MIME_TYPES = {
    ".mp3": ["audio/mpeg", "audio/mp3"],
    ".wav": ["audio/wav", "audio/x-wav", "audio/wave"],
    ".m4a": ["audio/mp4", "audio/x-m4a"],
    ".flac": ["audio/flac", "audio/x-flac"],
    ".ogg": ["audio/ogg", "application/ogg"],
    ".aac": ["audio/aac", "audio/x-aac"],
    ".wma": ["audio/x-ms-wma"],
    ".webm": ["audio/webm", "video/webm"],
    ".mp4": ["video/mp4", "audio/mp4"],
    ".mkv": ["video/x-matroska"]
}

# File signature (magic numbers) for common audio formats
AUDIO_SIGNATURES = {
    b"ID3": ".mp3",  # MP3 with ID3
    b"\xff\xfb": ".mp3",  # MP3
    b"\xff\xf3": ".mp3",  # MP3
    b"\xff\xf2": ".mp3",  # MP3
    b"RIFF": ".wav",  # WAV
    b"fLaC": ".flac",  # FLAC
    b"OggS": ".ogg",  # OGG
    b"\xff\xf1": ".aac",  # AAC
    b"\x00\x00\x00 ftyp": ".m4a",  # M4A/MP4
}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and injection.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    # Ensure filename is not empty
    if not filename:
        filename = "audio_file"
    
    return filename


def sanitize_subject(subject: Optional[str]) -> Optional[str]:
    """Sanitize subject field to prevent prompt injection.
    
    Args:
        subject: User-provided subject
        
    Returns:
        Sanitized subject string or None
    """
    if not subject:
        return None
    
    # Strip whitespace
    subject = subject.strip()
    
    # Remove control characters and excessive whitespace
    subject = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', subject)
    subject = re.sub(r'\s+', ' ', subject)
    
    # Limit length to prevent abuse
    max_length = 100
    if len(subject) > max_length:
        subject = subject[:max_length]
    
    # Remove potential prompt injection patterns
    dangerous_patterns = [
        r'ignore\s+previous',
        r'forget\s+everything',
        r'system\s*:',
        r'prompt\s*:',
        r'###',
        r'```'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, subject, re.IGNORECASE):
            logger.warning(f"Potential prompt injection detected in subject: {subject}")
            # Return a safe default
            return "general"
    
    # Only allow alphanumeric, spaces, and basic punctuation
    if not re.match(r'^[\w\s,.-]+$', subject):
        logger.warning(f"Invalid characters in subject: {subject}")
        return None
    
    return subject.lower()


def validate_file_extension(filename: str) -> str:
    """Validate file extension.
    
    Args:
        filename: File name to validate
        
    Returns:
        File extension
        
    Raises:
        ValidationError: If extension is invalid
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    if not file_ext:
        raise ValidationError(
            message="File must have an extension",
            error_code=ErrorCode.INVALID_FILE_FORMAT,
            details={"filename": filename}
        )
    
    if file_ext not in ALLOWED_AUDIO_FORMATS:
        raise ValidationError(
            message=f"Unsupported file format '{file_ext}'",
            error_code=ErrorCode.INVALID_FILE_FORMAT,
            details={
                "extension": file_ext,
                "allowed_formats": ALLOWED_AUDIO_FORMATS
            }
        )
    
    return file_ext


def validate_file_size(file_size: int) -> None:
    """Validate file size.
    
    Args:
        file_size: Size in bytes
        
    Raises:
        ValidationError: If file is too large
    """
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    
    if file_size > max_bytes:
        raise ValidationError(
            message=f"File too large ({file_size / 1024 / 1024:.1f}MB)",
            error_code=ErrorCode.FILE_TOO_LARGE,
            details={
                "size_mb": round(file_size / 1024 / 1024, 2),
                "max_mb": MAX_FILE_SIZE_MB
            }
        )


def verify_file_signature(file_path: str, expected_ext: str) -> bool:
    """Verify file type by checking magic number/signature.
    
    Args:
        file_path: Path to the file
        expected_ext: Expected file extension
        
    Returns:
        True if file signature matches extension
    """
    try:
        # Try using python-magic if available
        mime = magic.from_file(file_path, mime=True)
        
        # Check if MIME type matches expected extension
        expected_mimes = AUDIO_MIME_TYPES.get(expected_ext, [])
        if mime in expected_mimes:
            return True
        
        # Some audio files may be detected as generic types
        if mime in ["application/octet-stream", "audio/unknown"]:
            logger.warning(f"Could not determine MIME type, accepting based on extension")
            return True
        
        logger.warning(f"MIME type mismatch: expected {expected_mimes}, got {mime}")
        return False
        
    except ImportError:
        # python-magic not available, fall back to manual signature check
        logger.debug("python-magic not available, using manual signature check")
        return _check_signature_manual(file_path, expected_ext)
    except Exception as e:
        logger.error(f"Error verifying file signature: {str(e)}")
        return False


def _check_signature_manual(file_path: str, expected_ext: str) -> bool:
    """Manually check file signature without python-magic.
    
    Args:
        file_path: Path to the file
        expected_ext: Expected extension
        
    Returns:
        True if signature matches
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(32)  # Read first 32 bytes
        
        # Check against known signatures
        for signature, ext in AUDIO_SIGNATURES.items():
            if header.startswith(signature):
                return ext == expected_ext
        
        # If no signature matched, accept based on extension
        logger.warning(f"No matching signature found, accepting based on extension")
        return True
        
    except Exception as e:
        logger.error(f"Error reading file signature: {str(e)}")
        return False


def validate_ratio(ratio: float) -> float:
    """Validate summary ratio parameter.
    
    Args:
        ratio: Summary length ratio
        
    Returns:
        Validated ratio
        
    Raises:
        ValidationError: If ratio is invalid
    """
    if not 0.05 <= ratio <= 1.0:
        raise ValidationError(
            message=f"Invalid ratio {ratio}. Must be between 0.05 and 1.0",
            error_code=ErrorCode.INVALID_PARAMETERS,
            details={"ratio": ratio, "min": 0.05, "max": 1.0}
        )
    
    return ratio
