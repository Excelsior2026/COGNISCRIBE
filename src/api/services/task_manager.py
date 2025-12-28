"""Task manager for background processing with status tracking."""
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a processing task."""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Task metadata
    filename: Optional[str] = None
    file_size: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "error_code": self.error_code,
            "filename": self.filename,
            "file_size": self.file_size,
        }


class TaskManager:
    """Manages background processing tasks."""
    
    def __init__(self, max_tasks_in_memory: int = 1000):
        """
        Args:
            max_tasks_in_memory: Maximum number of tasks to keep in memory
        """
        self.tasks: Dict[str, Task] = {}
        self.max_tasks = max_tasks_in_memory
        self._lock = asyncio.Lock()
    
    async def create_task(self, filename: str = None, file_size: int = None) -> str:
        """Create a new task.
        
        Args:
            filename: Name of the file being processed
            file_size: Size of the file in bytes
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        async with self._lock:
            # Cleanup old tasks if needed
            if len(self.tasks) >= self.max_tasks:
                await self._cleanup_old_tasks()
            
            task = Task(
                task_id=task_id,
                filename=filename,
                file_size=file_size
            )
            self.tasks[task_id] = task
        
        logger.info(f"Created task {task_id} for file: {filename}")
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task object or None if not found
        """
        return self.tasks.get(task_id)
    
    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: float = None,
        error: str = None,
        error_code: str = None
    ) -> None:
        """Update task status.
        
        Args:
            task_id: The task ID
            status: New status
            progress: Optional progress (0.0 to 1.0)
            error: Optional error message
            error_code: Optional error code
        """
        task = await self.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for status update")
            return
        
        async with self._lock:
            task.status = status
            
            if progress is not None:
                task.progress = max(0.0, min(1.0, progress))
            
            if status == TaskStatus.PREPROCESSING and not task.started_at:
                task.started_at = datetime.utcnow()
            
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
                task.progress = 1.0
            
            if status == TaskStatus.FAILED:
                task.completed_at = datetime.utcnow()
                task.error = error
                task.error_code = error_code
        
        logger.debug(f"Task {task_id} status updated: {status.value} ({progress:.0%})") 
    
    async def set_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """Set task result.
        
        Args:
            task_id: The task ID
            result: Result data
        """
        task = await self.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for result update")
            return
        
        async with self._lock:
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.progress = 1.0
        
        logger.info(f"Task {task_id} completed successfully")
    
    async def _cleanup_old_tasks(self, keep_count: int = None) -> None:
        """Remove oldest completed/failed tasks.
        
        Args:
            keep_count: Number of tasks to keep (defaults to 75% of max)
        """
        if keep_count is None:
            keep_count = int(self.max_tasks * 0.75)
        
        # Get completed/failed tasks sorted by completion time
        finished_tasks = [
            (task_id, task)
            for task_id, task in self.tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            and task.completed_at
        ]
        
        if len(finished_tasks) <= keep_count:
            return
        
        # Sort by completion time (oldest first)
        finished_tasks.sort(key=lambda x: x[1].completed_at)
        
        # Remove oldest tasks
        remove_count = len(finished_tasks) - keep_count
        for i in range(remove_count):
            task_id = finished_tasks[i][0]
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {remove_count} old tasks")


# Global task manager instance
task_manager = TaskManager()
