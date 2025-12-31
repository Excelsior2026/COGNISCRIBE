"""Pydantic schemas for API request/response validation."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============= Request Models =============

class PipelineRequest(BaseModel):
    """Pipeline processing request (implicit - file upload)."""
    ratio: float = Field(0.15, ge=0.05, le=1.0, description="Summary length ratio")
    subject: Optional[str] = Field(None, description="Subject for customized summary")
    enhance: Optional[bool] = Field(None, description="Enable audio enhancement")
    async_mode: bool = Field(True, description="Process asynchronously")


# ============= Response Models =============

class TaskProgressResponse(BaseModel):
    """Task progress information."""
    stage: str = Field(..., description="Processing stage")
    percent: int = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Progress message")


class PipelineAsyncResponse(BaseModel):
    """Async pipeline response with task ID."""
    success: bool = True
    task_id: str = Field(..., description="Unique task identifier")
    status: str = "processing"
    message: str = "Audio processing started. Use GET /api/pipeline/{task_id} to check status."

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "message": "Audio processing started. Use GET /api/pipeline/{task_id} to check status."
            }
        }


class TranscriptSegment(BaseModel):
    """Individual transcript segment with timing."""
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Segment text")


class TranscriptResult(BaseModel):
    """Complete transcription result."""
    text: str = Field(..., description="Full transcript text")
    language: str = Field(..., description="Detected language (ISO 639-1)")
    duration: float = Field(..., description="Audio duration in seconds")
    segments: List[TranscriptSegment] = Field(..., description="Transcript segments with timestamps")


class SummarySections(BaseModel):
    """Structured summary sections."""
    learning_objectives: Optional[List[str]] = Field(None, description="Learning objectives")
    core_concepts: Optional[List[str]] = Field(None, description="Core concepts")
    clinical_terms: Optional[Dict[str, str]] = Field(None, description="Clinical terms and definitions")
    procedures: Optional[List[str]] = Field(None, description="Procedures and protocols")
    summary: Optional[str] = Field(None, description="Concise summary")


class PipelineMetadata(BaseModel):
    """Processing metadata."""
    filename: str
    duration: float
    language: str
    segments: int
    ratio: float
    subject: Optional[str] = None
    enhanced: bool
    enhancer: Optional[str] = None


class PipelineSyncResponse(BaseModel):
    """Synchronous pipeline response with full results."""
    success: bool = True
    transcription: str = Field(..., description="Full transcript text")
    transcript: TranscriptResult = Field(..., description="Complete transcription with segments")
    summary: SummarySections = Field(..., description="Structured summary")
    summary_text: str = Field(..., description="Raw summary text")
    metadata: PipelineMetadata = Field(..., description="Processing metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "transcription": "Today we discuss...",
                "transcript": {
                    "text": "Today we discuss...",
                    "language": "en",
                    "duration": 3600.0,
                    "segments": [
                        {"start": 0.0, "end": 30.5, "text": "Today we discuss..."}
                    ]
                },
                "summary": {
                    "learning_objectives": ["Understand X", "Learn Y"],
                    "core_concepts": ["Concept A", "Concept B"],
                    "summary": "Brief summary..."
                },
                "summary_text": "Brief summary...",
                "metadata": {
                    "filename": "lecture.mp3",
                    "duration": 3600.0,
                    "language": "en",
                    "segments": 120,
                    "ratio": 0.15,
                    "subject": "anatomy",
                    "enhanced": true,
                    "enhancer": "deepfilternet"
                }
            }
        }


class PipelineProgressResponse(BaseModel):
    """Task status and progress response."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Current task status")
    progress: TaskProgressResponse = Field(..., description="Progress information")
    created_at: str = Field(..., description="Task creation timestamp (ISO 8601)")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp (ISO 8601)")
    result: Optional[PipelineSyncResponse] = Field(None, description="Results (if completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    error_code: Optional[str] = Field(None, description="Error code")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": {
                    "stage": "transcribing",
                    "percent": 50,
                    "message": "Transcribing audio with Whisper"
                },
                "created_at": "2025-12-31T12:10:00Z",
                "completed_at": null,
                "result": null,
                "error": null,
                "error_code": null
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": false,
                "error": "file_too_large",
                "message": "File too large (501.5MB)",
                "details": {
                    "size_mb": 501.5,
                    "max_mb": 500
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-12-31T12:10:00Z"
            }
        }
