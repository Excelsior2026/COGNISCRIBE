"""Statistics and metrics endpoint."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.api.services.task_manager import task_manager
from src.middleware.rate_limit import get_rate_limit_stats
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_stats():
    """
    Get application statistics and metrics.
    
    Returns:
        Dictionary with statistics about:
        - Tasks (total, by status)
        - Rate limiting
        - System health
    """
    try:
        task_stats = task_manager.get_stats()
        rate_limit_stats = get_rate_limit_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "tasks": task_stats,
                "rate_limiting": rate_limit_stats,
                "status": "healthy"
            }
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "Failed to retrieve statistics"
            }
        )
