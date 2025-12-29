from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.api.services import transcriber
from src.utils.settings import OLLAMA_URL, OLLAMA_MODEL, WHISPER_MODEL, DEVICE
from src.utils.logger import setup_logger
import requests

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/health")
async def healthcheck():
    """
    Check health status of the API and its dependencies.
    
    Returns status of:
    - API service
    - Whisper model availability
    - Ollama service connectivity
    """
    status = {
        "status": "healthy",
        "whisper": {
            "model": WHISPER_MODEL,
            "device": DEVICE,
            "loaded": False
        },
        "ollama": {
            "url": OLLAMA_URL,
            "available": False
        }
    }
    
    # Check Whisper model
    try:
        transcriber.get_model()
        status["whisper"]["loaded"] = True
    except Exception as e:
        status["status"] = "degraded"
        status["whisper"]["error"] = str(e)
        logger.warning(f"Whisper health check failed: {str(e)}")
    
    # Check Ollama service
    try:
        tags_response = requests.get(
            OLLAMA_URL.replace("/api/generate", "/api/tags"),
            timeout=5,
        )

        if tags_response.status_code != 200:
            status["status"] = "degraded"
            status["ollama"]["error"] = f"Tags check returned {tags_response.status_code}"
        else:
            # Validate that the model runner can actually start (tags alone can be green
            # even when generation fails).
            generate_response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": "healthcheck",
                    "stream": False,
                    "options": {"num_predict": 1, "temperature": 0.0},
                },
                timeout=10,
            )

            if generate_response.status_code == 200:
                status["ollama"]["available"] = True
            else:
                status["status"] = "degraded"
                # Keep the error short; UI surfaces this.
                error_body = generate_response.text.strip()
                status["ollama"]["error"] = (
                    f"Generate check returned {generate_response.status_code}"
                    + (f": {error_body}" if error_body else "")
                )

    except Exception as e:
        status["status"] = "degraded"
        status["ollama"]["error"] = str(e)
        logger.warning(f"Ollama health check failed: {str(e)}")
    
    return JSONResponse(
        status_code=200 if status["status"] == "healthy" else 503,
        content=status
    )
