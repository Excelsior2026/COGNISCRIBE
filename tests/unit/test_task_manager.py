"""Unit tests for background task manager."""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.api.services.task_manager import (
    TaskManager, Task, TaskStatus, TaskProgress, ProcessingStage
)


class TestTaskCreation:
    """Test task creation and retrieval."""
    
    def test_create_task(self):
        """Test creating a new task."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) > 0
        
        # Task should exist in manager
        task = manager.get_task(task_id)
        assert task is not None
        assert task.task_id == task_id
    
    def test_task_initial_state(self):
        """Test initial task state."""
        manager = TaskManager()
        task_id = manager.create_task()
        task = manager.get_task(task_id)
        
        assert task.status == TaskStatus.PENDING
        assert task.progress.stage == ProcessingStage.UPLOADING
        assert task.progress.percent == 0
        assert task.result is None
        assert task.error is None
        assert task.completed_at is None
    
    def test_get_nonexistent_task(self):
        """Test retrieving non-existent task."""
        manager = TaskManager()
        task = manager.get_task("nonexistent-id")
        
        assert task is None
    
    def test_multiple_tasks(self):
        """Test creating multiple tasks."""
        manager = TaskManager()
        task_ids = [manager.create_task() for _ in range(5)]
        
        # All IDs should be unique
        assert len(set(task_ids)) == 5
        
        # All tasks should be retrievable
        for task_id in task_ids:
            task = manager.get_task(task_id)
            assert task is not None
            assert task.task_id == task_id


class TestTaskProgress:
    """Test task progress updates."""
    
    def test_update_progress_preprocessing(self):
        """Test updating progress to preprocessing stage."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        manager.update_progress(
            task_id,
            ProcessingStage.PREPROCESSING,
            25,
            "Preprocessing audio"
        )
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.PROCESSING
        assert task.progress.stage == ProcessingStage.PREPROCESSING
        assert task.progress.percent == 25
        assert task.progress.message == "Preprocessing audio"
    
    def test_update_progress_transcribing(self):
        """Test updating progress to transcribing stage."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        manager.update_progress(
            task_id,
            ProcessingStage.TRANSCRIBING,
            50,
            "Transcribing audio"
        )
        
        task = manager.get_task(task_id)
        assert task.progress.stage == ProcessingStage.TRANSCRIBING
        assert task.progress.percent == 50
    
    def test_update_progress_summarizing(self):
        """Test updating progress to summarizing stage."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        manager.update_progress(
            task_id,
            ProcessingStage.SUMMARIZING,
            75,
            "Generating summary"
        )
        
        task = manager.get_task(task_id)
        assert task.progress.stage == ProcessingStage.SUMMARIZING
        assert task.progress.percent == 75
    
    def test_update_progress_nonexistent_task(self):
        """Test updating non-existent task doesn't crash."""
        manager = TaskManager()
        
        # Should not raise
        manager.update_progress(
            "nonexistent-id",
            ProcessingStage.PREPROCESSING,
            50,
            "Test"
        )
    
    def test_progress_timestamps(self):
        """Test progress updates include timestamps."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        before = datetime.utcnow()
        manager.update_progress(
            task_id,
            ProcessingStage.PREPROCESSING,
            25,
            "Test"
        )
        after = datetime.utcnow()
        
        task = manager.get_task(task_id)
        assert before <= task.progress.updated_at <= after


class TestTaskCompletion:
    """Test task completion."""
    
    def test_complete_task(self):
        """Test completing a task with result."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        result = {
            "transcription": "Test transcription",
            "summary": "Test summary"
        }
        
        manager.complete_task(task_id, result)
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.completed_at is not None
        assert task.progress.stage == ProcessingStage.COMPLETED
        assert task.progress.percent == 100
    
    def test_complete_task_timestamp(self):
        """Test completion sets timestamp."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        before = datetime.utcnow()
        manager.complete_task(task_id, {"result": "test"})
        after = datetime.utcnow()
        
        task = manager.get_task(task_id)
        assert before <= task.completed_at <= after
    
    def test_complete_nonexistent_task(self):
        """Test completing non-existent task doesn't crash."""
        manager = TaskManager()
        
        # Should not raise
        manager.complete_task("nonexistent-id", {"result": "test"})


class TestTaskFailure:
    """Test task failure handling."""
    
    def test_fail_task(self):
        """Test failing a task with error."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        manager.fail_task(
            task_id,
            "Processing failed: test error",
            "TEST_ERROR_CODE"
        )
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.error == "Processing failed: test error"
        assert task.error_code == "TEST_ERROR_CODE"
        assert task.completed_at is not None
    
    def test_fail_task_without_error_code(self):
        """Test failing task without error code."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        manager.fail_task(task_id, "Generic error")
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.error == "Generic error"
        assert task.error_code is None
    
    def test_fail_nonexistent_task(self):
        """Test failing non-existent task doesn't crash."""
        manager = TaskManager()
        
        # Should not raise
        manager.fail_task("nonexistent-id", "Error")


class TestTaskCancellation:
    """Test task cancellation."""
    
    def test_cancel_pending_task(self):
        """Test cancelling a pending task."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        result = manager.cancel_task(task_id)
        
        assert result is True
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED
        assert task.completed_at is not None
    
    def test_cancel_processing_task(self):
        """Test cancelling a processing task."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        # Start processing
        manager.update_progress(task_id, ProcessingStage.PREPROCESSING, 25, "Test")
        
        result = manager.cancel_task(task_id)
        
        assert result is True
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED
    
    def test_cancel_completed_task(self):
        """Test cannot cancel completed task."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        # Complete task
        manager.complete_task(task_id, {"result": "test"})
        
        result = manager.cancel_task(task_id)
        
        assert result is False
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED  # Still completed
    
    def test_cancel_failed_task(self):
        """Test cannot cancel failed task."""
        manager = TaskManager()
        task_id = manager.create_task()
        
        # Fail task
        manager.fail_task(task_id, "Error")
        
        result = manager.cancel_task(task_id)
        
        assert result is False
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.FAILED  # Still failed
    
    def test_cancel_nonexistent_task(self):
        """Test cancelling non-existent task."""
        manager = TaskManager()
        
        result = manager.cancel_task("nonexistent-id")
        
        assert result is False


class TestTaskCleanup:
    """Test old task cleanup."""
    
    def test_cleanup_old_tasks(self):
        """Test cleanup removes old tasks."""
        manager = TaskManager()
        manager._task_retention = 60  # 60 seconds
        
        # Create tasks
        task_id1 = manager.create_task()
        task_id2 = manager.create_task()
        
        # Make task1 old
        task1 = manager.get_task(task_id1)
        task1.created_at = datetime.utcnow() - timedelta(seconds=120)
        
        # Run cleanup
        removed = manager.cleanup_old_tasks()
        
        assert removed == 1
        assert manager.get_task(task_id1) is None  # Removed
        assert manager.get_task(task_id2) is not None  # Still there
    
    def test_cleanup_no_old_tasks(self):
        """Test cleanup with no old tasks."""
        manager = TaskManager()
        manager._task_retention = 3600
        
        # Create recent tasks
        task_id = manager.create_task()
        
        removed = manager.cleanup_old_tasks()
        
        assert removed == 0
        assert manager.get_task(task_id) is not None
    
    def test_cleanup_all_old_tasks(self):
        """Test cleanup removes all old tasks."""
        manager = TaskManager()
        manager._task_retention = 60
        
        # Create multiple old tasks
        task_ids = [manager.create_task() for _ in range(5)]
        
        for task_id in task_ids:
            task = manager.get_task(task_id)
            task.created_at = datetime.utcnow() - timedelta(seconds=120)
        
        removed = manager.cleanup_old_tasks()
        
        assert removed == 5
        assert len(manager.tasks) == 0


class TestTaskStatistics:
    """Test task statistics."""
    
    def test_get_stats_empty(self):
        """Test statistics with no tasks."""
        manager = TaskManager()
        stats = manager.get_stats()
        
        assert stats["total_tasks"] == 0
        assert stats["status_breakdown"][TaskStatus.PENDING.value] == 0
    
    def test_get_stats_with_tasks(self):
        """Test statistics with various task statuses."""
        manager = TaskManager()
        
        # Create tasks in different states
        pending_id = manager.create_task()
        
        processing_id = manager.create_task()
        manager.update_progress(processing_id, ProcessingStage.PREPROCESSING, 25, "Test")
        
        completed_id = manager.create_task()
        manager.complete_task(completed_id, {"result": "test"})
        
        failed_id = manager.create_task()
        manager.fail_task(failed_id, "Error")
        
        stats = manager.get_stats()
        
        assert stats["total_tasks"] == 4
        assert stats["status_breakdown"][TaskStatus.PENDING.value] == 1
        assert stats["status_breakdown"][TaskStatus.PROCESSING.value] == 1
        assert stats["status_breakdown"][TaskStatus.COMPLETED.value] == 1
        assert stats["status_breakdown"][TaskStatus.FAILED.value] == 1
    
    def test_get_stats_retention_info(self):
        """Test statistics include retention info."""
        manager = TaskManager()
        stats = manager.get_stats()
        
        assert "retention_hours" in stats
        assert stats["retention_hours"] == manager._task_retention / 3600
