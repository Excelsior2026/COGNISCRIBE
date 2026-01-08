"""Task management with Redis and database persistence."""
from src.cache.redis_config import get_redis
from src.database.config import SessionLocal
from src.database.models import TranscriptionJob
from src.database.transactions import db_transaction
from datetime import datetime, timezone
from uuid import uuid4
import json

class TaskManager:
    """Manage transcription tasks with Redis cache and database persistence."""
    
    def __init__(self):
        self.redis = get_redis()
        self.db = SessionLocal()
    
    def create_task(self, user_id: str, filename: str, file_size_bytes: int, file_path: str, ratio: float) -> str:
        """Create new task in Redis and database."""
        task_id = str(uuid4())
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "filename": filename,
            "file_size_bytes": str(file_size_bytes),
            "file_path": file_path,
            "ratio": str(ratio),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "progress": "0"
        }
        
        # Store in Redis (24 hour TTL)
        self.redis.set_task(task_id, task_data, ttl=86400)
        
        # Store in database with transaction management
        with db_transaction() as db:
            db_task = TranscriptionJob(
                id=task_id,
                user_id=user_id,
                filename=filename,
                original_filename=filename,
                file_size_bytes=file_size_bytes,
                file_path=file_path,
                summary_ratio=ratio,
                status="pending"
            )
            db.add(db_task)
        
        return task_id
    
    def get_task(self, task_id: str) -> dict:
        """Get task from Redis (with database fallback)."""
        # Try Redis first
        task = self.redis.get_task(task_id)
        if task:
            return task
        
        # Fallback to database
        db_task = self.db.query(TranscriptionJob).filter(TranscriptionJob.id == task_id).first()
        if db_task:
            return {
                "task_id": db_task.id,
                "user_id": db_task.user_id,
                "filename": db_task.filename,
                "status": db_task.status,
                "progress": "0",
                "transcript_text": db_task.transcript_text or "",
                "summary_text": db_task.summary_text or "",
                "created_at": db_task.created_at.isoformat()
            }
        return None
    
    def update_task(self, task_id: str, data: dict) -> bool:
        """Update task in Redis and database."""
        # Update Redis
        self.redis.update_task(task_id, data)
        
        # Update database with transaction management
        with db_transaction() as db:
            db_task = db.query(TranscriptionJob).filter(TranscriptionJob.id == task_id).first()
            if db_task:
                if "status" in data:
                    db_task.status = data["status"]
                if "transcript_text" in data:
                    db_task.transcript_text = data["transcript_text"]
                if "summary_text" in data:
                    db_task.summary_text = data["summary_text"]
                if "progress" in data:
                    pass  # Progress is Redis-only
                
                db_task.updated_at = datetime.now(timezone.utc)
                return True
            return False
    
    def set_progress(self, task_id: str, progress: str) -> bool:
        """Update task progress (Redis only, fast)."""
        task = self.redis.get_task(task_id)
        if task:
            task["progress"] = progress
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            self.redis.update_task(task_id, task)
            return True
        return False
    
    def complete_task(self, task_id: str, transcript: str, summary: str, duration: float) -> bool:
        """Mark task as completed."""
        data = {
            "status": "completed",
            "transcript_text": transcript,
            "summary_text": summary,
            "duration": str(duration),
            "progress": "100",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update Redis
        self.redis.update_task(task_id, data)
        
        # Update database with transaction management
        with db_transaction() as db:
            db_task = db.query(TranscriptionJob).filter(TranscriptionJob.id == task_id).first()
            if db_task:
                db_task.status = "completed"
                db_task.transcript_text = transcript
                db_task.summary_text = summary
                db_task.transcript_duration = duration
                db_task.processing_completed_at = datetime.now(timezone.utc)
                return True
            return False
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark task as failed."""
        data = {
            "status": "failed",
            "error": error_message,
            "progress": "0",
            "failed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update Redis
        self.redis.update_task(task_id, data)
        
        # Update database with transaction management
        with db_transaction() as db:
            db_task = db.query(TranscriptionJob).filter(TranscriptionJob.id == task_id).first()
            if db_task:
                db_task.status = "failed"
                db_task.error_message = error_message
                db_task.processing_completed_at = datetime.now(timezone.utc)
                return True
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete task from Redis and database."""
        self.redis.delete_task(task_id)
        
        # Delete from database with transaction management
        with db_transaction() as db:
            db_task = db.query(TranscriptionJob).filter(TranscriptionJob.id == task_id).first()
            if db_task:
                db.delete(db_task)
                return True
            return False
    
    def close(self):
        """Close database connection."""
        self.db.close()
