"""
Streaming transcription endpoint for live preview during recording
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.services import transcriber
from src.utils.logger import setup_logger
import tempfile
import base64
import os

router = APIRouter(tags=["transcription"])
logger = setup_logger(__name__)


class AudioChunkRequest(BaseModel):
    audio: str  # Base64-encoded audio data
    timestamp: int  # Recording timestamp in seconds


@router.post("/transcribe-chunk")
async def transcribe_chunk(request: AudioChunkRequest):
    """
    Transcribe a single audio chunk for live preview.

    This provides a rough transcription quickly - optimized for speed over accuracy.
    Final transcription happens when full recording is processed.
    """
    temp_path = None

    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        logger.info(f"Transcribing audio chunk at timestamp {request.timestamp}s")

        # Quick transcription (no preprocessing, just raw Whisper)
        result = transcriber.transcribe_audio(temp_path)

        # Return just the text for live preview
        return {
            "success": True,
            "text": result.get("text", ""),
            "timestamp": request.timestamp,
        }

    except Exception as e:
        logger.error(f"Chunk transcription failed: {str(e)}")
        # Don't raise error - just return empty text so recording continues
        return {
            "success": False,
            "text": "",
            "error": str(e),
            "timestamp": request.timestamp,
        }

    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp chunk file: {e}")
