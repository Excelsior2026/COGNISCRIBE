"""Audit logging service for compliance and security."""
from src.database.config import SessionLocal
from src.database.models import AuditLog
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

class AuditLogger:
    """Log security and compliance events."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def log(
        self,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        details: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> str:
        """Log an audit event."""
        log_id = str(uuid4())
        
        audit_log = AuditLog(
            id=log_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details,
            error_message=error_message,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(audit_log)
        self.db.commit()
        return log_id
    
    def log_login(self, user_id: str, ip_address: str, user_agent: str, success: bool) -> str:
        """Log login attempt."""
        return self.log(
            action="login",
            resource_type="user",
            resource_id=user_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failure",
            details=f"Login attempt from {ip_address}"
        )
    
    def log_file_upload(self, user_id: str, task_id: str, filename: str, file_size: int, ip_address: str) -> str:
        """Log file upload."""
        return self.log(
            action="upload",
            resource_type="transcription_job",
            resource_id=task_id,
            user_id=user_id,
            ip_address=ip_address,
            status="success",
            details=f"Uploaded {filename} ({file_size} bytes)"
        )
    
    def log_transcription_complete(self, user_id: str, task_id: str, duration: float) -> str:
        """Log successful transcription."""
        return self.log(
            action="transcription_complete",
            resource_type="transcription_job",
            resource_id=task_id,
            user_id=user_id,
            status="success",
            details=f"Transcription completed in {duration:.2f} seconds"
        )
    
    def log_transcription_failed(self, user_id: str, task_id: str, error: str) -> str:
        """Log transcription failure."""
        return self.log(
            action="transcription_failed",
            resource_type="transcription_job",
            resource_id=task_id,
            user_id=user_id,
            status="failure",
            error_message=error,
            details=f"Transcription failed: {error}"
        )
    
    def close(self):
        """Close database connection."""
        self.db.close()
