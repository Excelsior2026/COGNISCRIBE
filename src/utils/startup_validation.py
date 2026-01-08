"""Startup validation and health checks for CogniScribe."""
import os
import sys
from typing import List, Tuple
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_environment() -> Tuple[bool, List[str]]:
    """Validate required environment variables and dependencies.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    warnings = []
    
    # Required environment variables
    required_vars = {
        "DATABASE_URL": "Database connection string",
        "JWT_SECRET_KEY": "JWT secret key for token signing"
    }
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing required environment variable: {var} ({description})")
        elif var == "JWT_SECRET_KEY" and value == "your-secret-key-change-in-production":
            errors.append(
                f"JWT_SECRET_KEY is set to default value. "
                f"Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
    
    # Optional but recommended
    if not os.getenv("CLINISCRIBE_API_KEYS"):
        warnings.append(
            "CLINISCRIBE_API_KEYS not set. A development key will be generated. "
            "Set this for production use."
        )
    
    # Check Redis availability (optional)
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        client = redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        logger.info("✅ Redis connection available")
    except Exception:
        warnings.append(
            f"Redis not available at {redis_url}. "
            "Rate limiting will use in-memory storage (not suitable for multi-instance deployments)."
        )
    
    # Check database connectivity
    try:
        from src.database.config import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
    except Exception as e:
        errors.append(f"Database connection failed: {str(e)}")
    
    # Check Ollama availability (optional, but important for functionality)
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    ollama_port = os.getenv("OLLAMA_PORT", "11434")
    try:
        import requests
        response = requests.get(
            f"http://{ollama_host}:{ollama_port}/api/tags",
            timeout=2
        )
        if response.status_code == 200:
            logger.info("✅ Ollama service available")
        else:
            warnings.append(
                f"Ollama service at {ollama_host}:{ollama_port} returned status {response.status_code}. "
                "Summarization will not work."
            )
    except Exception:
        warnings.append(
            f"Ollama service not available at {ollama_host}:{ollama_port}. "
            "Summarization will not work. Install and start Ollama to enable this feature."
        )
    
    # Display warnings
    if warnings:
        logger.warning("⚠️  Startup Warnings:")
        for warning in warnings:
            logger.warning(f"   - {warning}")
    
    # Display errors
    if errors:
        logger.error("❌ Startup Errors:")
        for error in errors:
            logger.error(f"   - {error}")
        logger.error("\nPlease fix the errors above before starting the application.")
        return False, errors
    
    logger.info("✅ Environment validation passed")
    return True, []


def check_directories() -> None:
    """Check and create required directories."""
    from src.utils.settings import (
        AUDIO_STORAGE_DIR,
        TEMP_AUDIO_DIR,
        get_settings
    )
    
    settings = get_settings()
    
    directories = [
        ("Audio storage", AUDIO_STORAGE_DIR),
        ("Temporary audio", TEMP_AUDIO_DIR),
    ]
    
    for name, path in directories:
        try:
            os.makedirs(path, exist_ok=True)
            logger.debug(f"✅ {name} directory ready: {path}")
        except Exception as e:
            logger.warning(f"⚠️  Could not create {name} directory {path}: {e}")


def print_startup_info() -> None:
    """Print helpful startup information."""
    from src.utils.settings import (
        API_TITLE,
        API_VERSION,
        get_settings
    )
    
    settings = get_settings()
    
    print("\n" + "="*60)
    print(f"🚀 {API_TITLE} v{API_VERSION}")
    print("="*60)
    print(f"📁 Data directory: {settings.base_data_dir}")
    print(f"🎙️  Audio storage: {settings.resolved_audio_storage_dir}")
    print(f"📝 Temp directory: {settings.resolved_temp_audio_dir}")
    print(f"🤖 Ollama: {settings.ollama_url}")
    print(f"🔊 Whisper model: {settings.whisper_model} ({settings.device})")
    print(f"🔒 PHI detection: {'Enabled' if settings.phi_detection_enabled else 'Disabled'}")
    print(f"📊 Rate limiting: {'Enabled' if os.getenv('CLINISCRIBE_RATE_LIMIT_ENABLED', 'true').lower() in ('true', '1', 'yes') else 'Disabled'}")
    print("="*60 + "\n")


def validate_on_startup() -> bool:
    """Run all startup validations.
    
    Returns:
        True if validation passed, False otherwise
    """
    print_startup_info()
    
    is_valid, errors = validate_environment()
    
    if not is_valid:
        return False
    
    check_directories()
    
    logger.info("✅ CogniScribe startup validation complete")
    return True
