import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from src.api.services import audio_preprocess, transcriber, summarizer
from src.utils.settings import AUDIO_STORAGE_DIR, MAX_FILE_SIZE_MB, ALLOWED_AUDIO_FORMATS
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


def validate_audio_file(file: UploadFile) -> None:
    """Validate uploaded audio file."""
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. "
                   f"Allowed formats: {', '.join(ALLOWED_AUDIO_FORMATS)}"
        )
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size:
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file.size / 1024 / 1024:.1f}MB). "
                       f"Maximum allowed: {MAX_FILE_SIZE_MB}MB"
            )


@router.post("/pipeline")
async def pipeline(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    ratio: float = Query(0.15, ge=0.05, le=1.0, description="Summary length ratio (0.05-1.0)"),
    subject: Optional[str] = Query(None, description="Optional subject/topic (e.g., 'anatomy', 'pharmacology')")
):
    """
    Process audio file through complete pipeline:
    1. Upload and validate
    2. Preprocess (noise reduction, normalization)
    3. Transcribe with Whisper
    4. Generate structured summary with Ollama
    
    Returns transcription and formatted study notes.
    """
    logger.info(f"Pipeline request: {file.filename} (ratio={ratio}, subject={subject})")
    
    raw_path = None
    clean_path = None
    
    try:
        # Validate file
        validate_audio_file(file)
        
        # Create storage directory
        date_dir = datetime.utcnow().strftime("%Y-%m-%d")
        storage_path = os.path.join(AUDIO_STORAGE_DIR, date_dir)
        os.makedirs(storage_path, exist_ok=True)
        
        # Save uploaded file
        raw_path = os.path.join(storage_path, f"{uuid.uuid4()}_{file.filename}")
        logger.debug(f"Saving uploaded file to: {raw_path}")
        
        content = await file.read()
        with open(raw_path, "wb") as f:
            f.write(content)
        
        # Stage 1: Preprocess audio
        logger.info("Stage 1/3: Preprocessing audio...")
        clean_path = audio_preprocess.preprocess_audio(raw_path)
        
        # Stage 2: Transcribe
        logger.info("Stage 2/3: Transcribing audio...")
        transcript = transcriber.transcribe_audio(clean_path)
        
        # Stage 3: Summarize
        logger.info("Stage 3/3: Generating summary...")
        summary = summarizer.generate_summary(
            transcript["text"],
            ratio=ratio,
            subject=subject
        )
        
        # Cleanup temporary processed file
        audio_preprocess.cleanup_temp_file(clean_path)
        
        logger.info(f"Pipeline completed successfully for {file.filename}")
        
        return {
            "success": True,
            "transcript": transcript,
            "summary": summary,
            "metadata": {
                "filename": file.filename,
                "duration": transcript["duration"],
                "language": transcript["language"],
                "segments": len(transcript["segments"]),
                "ratio": ratio,
                "subject": subject
            }
        }
        
    except HTTPException:
        # Re-raise validation errors
        raise
        
    except Exception as e:
        logger.error(f"Pipeline failed for {file.filename}: {str(e)}")
        
        # Cleanup on failure
        if clean_path:
            audio_preprocess.cleanup_temp_file(clean_path)
        
        # Return user-friendly error
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to process audio. Please check the file and try again."
            }
        )
