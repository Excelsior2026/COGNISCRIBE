import asyncio
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routers.pipeline import router as pipeline_router
from src.api.routers.healthcheck import router as health_router
from src.api.routers.transcribe_chunk import router as transcribe_router
from src.api.services.cleanup import cleanup_old_audio
from src.api.services.task_manager import task_manager
from src.middleware.auth import authenticate_request
from src.middleware.rate_limit import rate_limit_middleware, cleanup_old_entries
from src.utils.settings import (
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
)
from src.utils.errors import CliniScribeException
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


# Global exception handler for CliniScribe exceptions
@app.exception_handler(CliniScribeException)
async def cliniscribe_exception_handler(request: Request, exc: CliniScribeException):
    """Handle CliniScribe custom exceptions."""
    logger.error(f"CliniScribe exception: {exc.message} (code: {exc.error_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error_code.value,
            "message": exc.message,
            **exc.details
        }
    )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Request middleware for auth and rate limiting
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Apply authentication and rate limiting to requests."""
    try:
        # Skip middleware for health check
        if request.url.path in ["/health", "/api/health"]:
            response = await call_next(request)
            return response
        
        # Apply rate limiting
        await rate_limit_middleware(request)
        
        # Apply authentication
        await authenticate_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers if available
        if hasattr(request.state, 'rate_limit_limit'):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
        
        return response
        
    except CliniScribeException as exc:
        # Let CliniScribe exceptions pass through to exception handler
        raise exc.to_http_exception()


# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(pipeline_router, prefix="/api", tags=["Pipeline"])
app.include_router(transcribe_router, prefix="/api", tags=["Transcription"])


# Background cleanup tasks
cleanup_task = None
rate_limit_cleanup_task = None
task_cleanup_task = None


async def run_daily_cleanup():
    """Run audio file cleanup task daily in background."""
    while True:
        try:
            await asyncio.sleep(86400)  # 24 hours
            cleanup_old_audio()
            logger.info("Daily audio cleanup completed")
        except Exception as e:
            logger.error(f"Scheduled audio cleanup failed: {str(e)}")


async def run_rate_limit_cleanup():
    """Run rate limit cleanup every 5 minutes."""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            cleaned = cleanup_old_entries()
            if cleaned > 0:
                logger.debug(f"Cleaned up {cleaned} rate limit entries")
        except Exception as e:
            logger.error(f"Rate limit cleanup failed: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global cleanup_task, rate_limit_cleanup_task, task_cleanup_task
    
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")
    logger.info(f"CORS origins: {CORS_ALLOW_ORIGINS}")

    # Start background cleanup tasks
    cleanup_task = asyncio.create_task(run_daily_cleanup())
    rate_limit_cleanup_task = asyncio.create_task(run_rate_limit_cleanup())
    task_cleanup_task = asyncio.create_task(task_manager.start_cleanup_worker())

    logger.info("Application startup complete")
    logger.info("API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    global cleanup_task, rate_limit_cleanup_task, task_cleanup_task
    
    logger.info("Shutting down application...")
    
    # Cancel background tasks
    if cleanup_task:
        cleanup_task.cancel()
    if rate_limit_cleanup_task:
        rate_limit_cleanup_task.cancel()
    if task_cleanup_task:
        task_cleanup_task.cancel()
    
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    import os

    # Get configuration from environment variables
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "127.0.0.1")
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        access_log=True
    )
