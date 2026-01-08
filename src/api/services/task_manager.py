"""Background task manager for async audio processing."""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskStatus(str, Enum):
    """Status of a background task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(str, Enum):
    """Processing stages for pipeline."""
    UPLOADING = "uploading"
    PREPROCESSING = "preprocessing"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"


@dataclass
class TaskProgress:
    """Progress information for a task."""
    stage: ProcessingStage
    percent: int = 0
    message: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Task:
    """Background task information."""
    task_id: str
    status: TaskStatus
    progress: TaskProgress
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class TaskManager:
    """Manages background tasks for audio processing."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._cleanup_interval = 3600  # Clean up old tasks every hour
        self._task_retention = 86400  # Keep tasks for 24 hours
        self._max_tasks = int(os.getenv("COGNISCRIBE_MAX_TASKS", "10000"))  # Maximum tasks in memory
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=TaskProgress(
                stage=ProcessingStage.UPLOADING,
                percent=0,
                message="Task created"
            )
        )
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def update_progress(
        self,
        task_id: str,
        stage: ProcessingStage,
        percent: int,
        message: str = ""
    ) -> None:
        """Update task progress."""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Attempted to update non-existent task {task_id}")
            return
        
        task.status = TaskStatus.PROCESSING
        task.progress = TaskProgress(
            stage=stage,
            percent=percent,
            message=message
        )
        logger.debug(f"Task {task_id}: {stage.value} - {percent}% - {message}")
    
    def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Mark task as completed with result."""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Attempted to complete non-existent task {task_id}")
            return
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.result = result
        task.progress = TaskProgress(
            stage=ProcessingStage.COMPLETED,
            percent=100,
            message="Processing completed successfully"
        )
        logger.info(f"Task {task_id} completed successfully")
    
    def fail_task(
        self,
        task_id: str,
        error: str,
        error_code: Optional[str] = None
    ) -> None:
        """Mark task as failed with error."""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Attempted to fail non-existent task {task_id}")
            return
        
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now(timezone.utc)
        task.error = error
        task.error_code = error_code
        logger.error(f"Task {task_id} failed: {error}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or processing task."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc)
        logger.info(f"Task {task_id} cancelled")
        return True
    
    def cleanup_old_tasks(self) -> int:
        """Remove tasks older than retention period.
        
        Also removes failed/cancelled tasks more aggressively to prevent memory bloat.
        """
        cutoff = datetime.now(timezone.utc).timestamp() - self._task_retention
        failed_cutoff = datetime.now(timezone.utc).timestamp() - (self._task_retention / 4)  # Keep failed tasks for 6 hours
        
        removed = 0
        
        for task_id in list(self.tasks.keys()):
            task = self.tasks[task_id]
            task_age = task.created_at.timestamp()
            
            # Remove old tasks
            if task_age < cutoff:
                del self.tasks[task_id]
                removed += 1
            # Remove failed/cancelled tasks more aggressively
            elif task.status in [TaskStatus.FAILED, TaskStatus.CANCELLED] and task_age < failed_cutoff:
                del self.tasks[task_id]
                removed += 1
        
        # If still over limit, remove oldest completed tasks
        if len(self.tasks) > self._max_tasks:
            sorted_tasks = sorted(
                self.tasks.items(),
                key=lambda x: x[1].created_at.timestamp()
            )
            excess = len(self.tasks) - self._max_tasks
            for task_id, _ in sorted_tasks[:excess]:
                if self.tasks[task_id].status == TaskStatus.COMPLETED:
                    del self.tasks[task_id]
                    removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old tasks (remaining: {len(self.tasks)})")
        
        return removed
    
    async def start_cleanup_worker(self) -> None:
        """Start background worker for cleaning up old tasks."""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            try:
                self.cleanup_old_tasks()
            except Exception as e:
                logger.error(f"Task cleanup failed: {str(e)}")
    
    def get_stats(self) -> dict:
        """Get task manager statistics."""
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in self.tasks.values():
            status_counts[task.status.value] += 1
        
        return {
            "total_tasks": len(self.tasks),
            "status_breakdown": status_counts,
            "retention_hours": self._task_retention / 3600
        }


# Global task manager instance
task_manager = TaskManager()
