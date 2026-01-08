"""Retry utilities for external service calls."""
import asyncio
import time
from typing import Callable, TypeVar, Optional, List, Type
from functools import wraps
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or [Exception]


def retry_with_backoff(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None
) -> Callable[..., T]:
    """Decorator to retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        config: Retry configuration
        
    Returns:
        Wrapped function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except tuple(config.retryable_exceptions) as e:
                last_exception = e
                
                if attempt == config.max_attempts:
                    logger.error(
                        f"Function {func.__name__} failed after {config.max_attempts} attempts: {str(e)}"
                    )
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(
                    config.initial_delay * (config.exponential_base ** (attempt - 1)),
                    config.max_delay
                )
                
                logger.warning(
                    f"Function {func.__name__} failed (attempt {attempt}/{config.max_attempts}): {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic failed unexpectedly")
    
    return wrapper


async def retry_async_with_backoff(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None
) -> Callable[..., T]:
    """Async decorator to retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        config: Retry configuration
        
    Returns:
        Wrapped async function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except tuple(config.retryable_exceptions) as e:
                last_exception = e
                
                if attempt == config.max_attempts:
                    logger.error(
                        f"Async function {func.__name__} failed after {config.max_attempts} attempts: {str(e)}"
                    )
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(
                    config.initial_delay * (config.exponential_base ** (attempt - 1)),
                    config.max_delay
                )
                
                logger.warning(
                    f"Async function {func.__name__} failed (attempt {attempt}/{config.max_attempts}): {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic failed unexpectedly")
    
    return wrapper
