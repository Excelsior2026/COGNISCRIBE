"""Track usage statistics for analytics and billing."""
from src.database.config import SessionLocal
from src.database.models import UsageStatistics
from datetime import datetime, timezone
from uuid import uuid4

class UsageTracker:
    """Track user usage statistics."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def get_or_create_monthly_stats(self, user_id: str) -> UsageStatistics:
        """Get or create usage stats for current month."""
        now = datetime.now(timezone.utc)
        month = f"{now.year:04d}-{now.month:02d}"
        
        stats = self.db.query(UsageStatistics).filter(
            UsageStatistics.user_id == user_id,
            UsageStatistics.month == month
        ).first()
        
        if not stats:
            stats = UsageStatistics(
                id=str(uuid4()),
                user_id=user_id,
                month=month
            )
            self.db.add(stats)
            self.db.commit()
        
        return stats
    
    def record_successful_job(self, user_id: str, bytes_processed: int, processing_seconds: float) -> bool:
        """Record successful transcription job."""
        stats = self.get_or_create_monthly_stats(user_id)
        
        stats.total_files_processed += 1
        stats.total_bytes_processed += bytes_processed
        stats.total_processing_seconds += processing_seconds
        stats.successful_jobs += 1
        stats.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        return True
    
    def record_failed_job(self, user_id: str) -> bool:
        """Record failed transcription job."""
        stats = self.get_or_create_monthly_stats(user_id)
        
        stats.failed_jobs += 1
        stats.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        return True
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get current month statistics for user."""
        now = datetime.now(timezone.utc)
        month = f"{now.year:04d}-{now.month:02d}"
        
        stats = self.db.query(UsageStatistics).filter(
            UsageStatistics.user_id == user_id,
            UsageStatistics.month == month
        ).first()
        
        if stats:
            return {
                "files_processed": stats.total_files_processed,
                "bytes_processed": stats.total_bytes_processed,
                "processing_seconds": stats.total_processing_seconds,
                "successful_jobs": stats.successful_jobs,
                "failed_jobs": stats.failed_jobs,
                "month": month
            }
        return {
            "files_processed": 0,
            "bytes_processed": 0,
            "processing_seconds": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "month": month
        }
    
    def close(self):
        """Close database connection."""
        self.db.close()
