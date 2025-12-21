import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers.pipeline import router as pipeline_router
from src.api.routers.healthcheck import router as health_router
from src.api.routers.transcribe_chunk import router as transcribe_router
from src.api.services.cleanup import cleanup_old_audio
from src.utils.settings import API_TITLE, API_VERSION, API_DESCRIPTION
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
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(pipeline_router, prefix="/api", tags=["Pipeline"])
app.include_router(transcribe_router, prefix="/api", tags=["Transcription"])

# Background cleanup task
cleanup_task = None

async def run_daily_cleanup():
    """Run cleanup task daily in background."""
    while True:
        try:
            await asyncio.sleep(86400)  # 24 hours
            cleanup_old_audio()
            logger.info("Daily cleanup completed")
        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global cleanup_task
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(run_daily_cleanup())

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    global cleanup_task
    if cleanup_task:
        cleanup_task.cancel()
    logger.info("Application shutting down")
