import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from src.api.services import audio_preprocess, transcriber, summarizer
from src.api.services import reasoning
from src.api.services.task_manager import task_manager, ProcessingStage
from src.utils.settings import (
    AUDIO_STORAGE_DIR,
    MAX_FILE_SIZE_MB,
    ALLOWED_AUDIO_FORMATS,
    DEEPFILTERNET_ENABLED,
    REASONING_CORE_ENABLED,
    REASONING_CORE_DOMAIN,
)
from src.utils.validation import (
    sanitize_filename,
    sanitize_subject,
    validate_file_extension,
    validate_file_size,
    validate_ratio,
    verify_file_signature,
)
from src.utils.errors import (
    CliniScribeException,
    ValidationError,
    ProcessingError,
    ServiceUnavailableError,
    ErrorCode,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


def validate_audio_file(file: UploadFile) -> str:
    """Validate uploaded audio file.
    
    Returns:
        Sanitized filename
        
    Raises:
        ValidationError: If file is invalid
    """
    # Get and sanitize filename
    filename = sanitize_filename(file.filename or "audio")
    
    # Validate extension
    file_ext = validate_file_extension(filename)
    
    # Check file size if available
    if hasattr(file, 'size') and file.size:
        validate_file_size(file.size)
    
    return filename


async def process_pipeline_task(
    task_id: str,
    raw_path: str,
    filename: str,
    ratio: float,
    subject: Optional[str],
    use_deepfilter: bool,
    include_reasoning: bool,
    reasoning_domain: Optional[str],
) -> None:
    """Process audio pipeline in background.
    
    Args:
        task_id: Unique task identifier
        raw_path: Path to uploaded audio file
        filename: Original filename
        ratio: Summary length ratio
        subject: Optional subject for tailored summary
        use_deepfilter: Whether to use DeepFilterNet enhancement
    """
    clean_path = None
    
    try:
        # Stage 1: Preprocess audio
        task_manager.update_progress(
            task_id,
            ProcessingStage.PREPROCESSING,
            25,
            "Cleaning and normalizing audio"
        )
        
        clean_path, preprocess_meta = await asyncio.to_thread(
            audio_preprocess.preprocess_audio,
            raw_path,
            use_deepfilter=use_deepfilter,
        )
        
        # Stage 2: Transcribe
        task_manager.update_progress(
            task_id,
            ProcessingStage.TRANSCRIBING,
            50,
            "Transcribing audio with Whisper"
        )
        
        transcript = await asyncio.to_thread(
            transcriber.transcribe_audio,
            clean_path
        )
        
        # Stage 3: Summarize
        task_manager.update_progress(
            task_id,
            ProcessingStage.SUMMARIZING,
            75,
            "Generating structured study notes"
        )
        
        summary_text = await asyncio.to_thread(
            summarizer.generate_summary,
            transcript["text"],
            ratio=ratio,
            subject=subject
        )
        summary_sections = summarizer.parse_summary_sections(summary_text)

        reasoning_result = None
        if include_reasoning:
            task_manager.update_progress(
                task_id,
                ProcessingStage.REASONING,
                90,
                "Extracting concepts and relationships"
            )
            reasoning_result = await asyncio.to_thread(
                reasoning.analyze_text,
                transcript["text"],
                reasoning_domain,
                include_reasoning,
            )
        
        # Cleanup temporary processed file
        if clean_path:
            audio_preprocess.cleanup_temp_file(clean_path)
        
        # Complete task
        result = {
            "success": True,
            "transcription": transcript["text"],
            "transcript": transcript,
            "summary": summary_sections,
            "summary_text": summary_text,
            "reasoning": reasoning_result,
            "metadata": {
                "filename": filename,
                "duration": transcript["duration"],
                "language": transcript["language"],
                "segments": len(transcript["segments"]),
                "ratio": ratio,
                "subject": subject,
                "enhanced": preprocess_meta["enhanced"],
                "enhancer": preprocess_meta["enhancer"],
            }
        }
        
        task_manager.complete_task(task_id, result)
        logger.info(f"Pipeline completed successfully for task {task_id}")
        
    except CliniScribeException as exc:
        logger.error(f"Pipeline failed for task {task_id}: {exc.message}")

        # Cleanup on failure
        if clean_path:
            audio_preprocess.cleanup_temp_file(clean_path)

        task_manager.fail_task(
            task_id,
            error=exc.message,
            error_code=exc.error_code.value,
        )

    except Exception as e:
        logger.error(f"Pipeline failed for task {task_id}: {str(e)}")

        # Cleanup on failure
        if clean_path:
            audio_preprocess.cleanup_temp_file(clean_path)

        # Determine error code
        error_code = ErrorCode.UNKNOWN_ERROR
        if "transcrib" in str(e).lower():
            error_code = ErrorCode.TRANSCRIPTION_FAILED
        elif "summar" in str(e).lower() or "ollama" in str(e).lower():
            error_code = ErrorCode.SUMMARIZATION_FAILED
        elif "preprocess" in str(e).lower():
            error_code = ErrorCode.PREPROCESSING_FAILED
        
        task_manager.fail_task(
            task_id,
            error=str(e),
            error_code=error_code.value
        )


@router.post("/pipeline")
async def pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to transcribe"),
    ratio: float = Query(0.15, ge=0.05, le=1.0, description="Summary length ratio (0.05-1.0)"),
    subject: Optional[str] = Query(None, description="Optional subject/topic (e.g., 'anatomy', 'pharmacology')"),
    enhance: Optional[bool] = Query(
        None,
        description="Enable DeepFilterNet enhancement if available (defaults to server setting).",
    ),
    include_reasoning: bool = Query(
        REASONING_CORE_ENABLED,
        description="Also run reasoning-core to extract concepts, relationships, and knowledge graph.",
    ),
    reasoning_domain: Optional[str] = Query(
        None,
        description="Optional reasoning-core domain (medical, business, meeting, generic).",
    ),
    async_mode: bool = Query(
        True,
        description="Process asynchronously (recommended for large files)"
    )
):
    """
    Process audio file through complete pipeline:
    1. Upload and validate
    2. Preprocess (noise reduction, normalization, optional enhancement)
    3. Transcribe with Whisper
    4. Generate structured summary with Ollama
    
    Returns task_id for async processing, or immediate results for sync mode.
    """
    logger.info(f"Pipeline request: {file.filename} (ratio={ratio}, subject={subject}, enhance={enhance}, async={async_mode})")
    
    raw_path = None
    
    try:
        # Validate file
        filename = validate_audio_file(file)
        
        # Validate and sanitize other parameters
        ratio = validate_ratio(ratio)
        subject = sanitize_subject(subject)
        
        # Create storage directory
        date_dir = datetime.utcnow().strftime("%Y-%m-%d")
        storage_path = os.path.join(AUDIO_STORAGE_DIR, date_dir)
        os.makedirs(storage_path, exist_ok=True)
        
        # Save uploaded file
        raw_path = os.path.join(storage_path, f"{uuid.uuid4()}_{filename}")
        logger.debug(f"Saving uploaded file to: {raw_path}")

        # Stream file to disk with size validation
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        total_bytes = 0
        with open(raw_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise ValidationError(
                        message=f"File too large ({total_bytes / 1024 / 1024:.1f}MB)",
                        error_code=ErrorCode.FILE_TOO_LARGE,
                        details={
                            "size_mb": round(total_bytes / 1024 / 1024, 2),
                            "max_mb": MAX_FILE_SIZE_MB
                        }
                    )
                f.write(chunk)

        await file.close()
        
        # Verify file signature
        file_ext = os.path.splitext(filename)[1].lower()
        if not verify_file_signature(raw_path, file_ext):
            logger.warning(f"File signature mismatch for {filename}")
            # Continue anyway, but log the warning
        
        # Determine enhancement setting
        use_deepfilter = DEEPFILTERNET_ENABLED if enhance is None else enhance
        
        # Async mode: Create task and process in background
        if async_mode:
            task_id = task_manager.create_task()
            
            # Queue background processing
            background_tasks.add_task(
                process_pipeline_task,
                task_id,
                raw_path,
                filename,
                ratio,
                subject,
                use_deepfilter,
                include_reasoning,
                reasoning_domain or REASONING_CORE_DOMAIN,
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "status": "processing",
                "message": "Audio processing started. Use GET /api/pipeline/{task_id} to check status."
            }
        
        # Sync mode: Process immediately (for smaller files)
        else:
            task_id = task_manager.create_task()
            await process_pipeline_task(
                task_id,
                raw_path,
                filename,
                ratio,
                subject,
                use_deepfilter,
                include_reasoning,
                reasoning_domain or REASONING_CORE_DOMAIN,
            )
            
            task = task_manager.get_task(task_id)
            if task and task.result:
                return task.result
            elif task and task.error:
                raise ProcessingError(
                    message=task.error,
                    error_code=ErrorCode(task.error_code) if task.error_code else ErrorCode.UNKNOWN_ERROR
                )
            else:
                raise ProcessingError(
                    message="Processing failed with unknown error",
                    error_code=ErrorCode.UNKNOWN_ERROR
                )
        
    except ValidationError:
        # Cleanup on validation error
        if raw_path and os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except Exception:
                pass
        raise
        
    except Exception as e:
        logger.error(f"Pipeline request failed: {str(e)}")
        
        # Cleanup on failure
        if raw_path and os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except Exception:
                pass
        
        # Re-raise CliniScribe exceptions
        if isinstance(e, (ValidationError, ProcessingError, ServiceUnavailableError)):
            raise
        
        # Convert to generic processing error
        raise ProcessingError(
            message="Failed to process audio. Please check the file and try again.",
            error_code=ErrorCode.INTERNAL_ERROR
        )


@router.get("/pipeline/{task_id}")
async def get_pipeline_status(task_id: str):
    """
    Get status and results of a pipeline task.
    
    Returns task status, progress, and results if completed.
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": f"Task {task_id} not found"
            }
        )
    
    response = {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": {
            "stage": task.progress.stage.value,
            "percent": task.progress.percent,
            "message": task.progress.message,
        },
        "created_at": task.created_at.isoformat(),
    }
    
    if task.completed_at:
        response["completed_at"] = task.completed_at.isoformat()
    
    if task.result:
        response["result"] = task.result
    
    if task.error:
        response["error"] = task.error
        response["error_code"] = task.error_code
    
    return response


@router.delete("/pipeline/{task_id}")
async def cancel_pipeline_task(task_id: str):
    """
    Cancel a pending or processing task.
    """
    cancelled = task_manager.cancel_task(task_id)
    
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "cannot_cancel",
                "message": "Task cannot be cancelled (not found or already completed)"
            }
        )
    
    return {
        "success": True,
        "message": f"Task {task_id} cancelled"
    }
