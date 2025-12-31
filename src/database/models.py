"""SQLAlchemy ORM models for COGNISCRIBE."""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class TranscriptionJob(Base):
    """Transcription job tracking."""
    __tablename__ = "transcription_jobs"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    summary_ratio = Column(Float, default=0.15)
    async_mode = Column(Boolean, default=True)
    
    # Results
    transcript_text = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=True)
    transcript_duration = Column(Float, nullable=True)
    segment_count = Column(Integer, nullable=True)
    
    # Processing info
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    language_detected = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TranscriptionJob(id='{self.id}', status='{self.status}')>"


class AuditLog(Base):
    """Audit trail for security and compliance."""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), index=True, nullable=True)
    action = Column(String(50), index=True, nullable=False)  # login, register, upload, download, etc
    resource_type = Column(String(50), nullable=True)  # user, transcription_job, etc
    resource_id = Column(String(36), index=True, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False)  # success, failure
    details = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', status='{self.status}')>"


class UsageStatistics(Base):
    """Track usage for billing and analytics."""
    __tablename__ = "usage_statistics"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # Monthly tracking (reset monthly)
    month = Column(String(7), index=True)  # YYYY-MM format
    
    # Aggregated statistics
    total_files_processed = Column(Integer, default=0)
    total_bytes_processed = Column(Integer, default=0)
    total_processing_seconds = Column(Float, default=0.0)
    successful_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    
    # Cost tracking (if implementing billing)
    estimated_cost_cents = Column(Integer, default=0)  # in cents
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UsageStatistics(user_id='{self.user_id}', month='{self.month}')>"
