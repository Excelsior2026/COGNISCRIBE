"""Tests for database operations."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, User, TranscriptionJob, AuditLog
from src.database.config import SessionLocal
from src.api.middleware.jwt_auth import hash_password
from uuid import uuid4
from datetime import datetime

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, test_db):
        """Test user creation."""
        user = User(
            id=str(uuid4()),
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("testpass123"),
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        db_user = test_db.query(User).filter(User.username == "testuser").first()
        assert db_user is not None
        assert db_user.email == "test@example.com"
        assert db_user.is_active is True
    
    def test_user_unique_username(self, test_db):
        """Test username uniqueness."""
        user1 = User(
            id=str(uuid4()),
            username="unique_user",
            email="user1@example.com",
            hashed_password=hash_password("pass123")
        )
        test_db.add(user1)
        test_db.commit()
        
        user2 = User(
            id=str(uuid4()),
            username="unique_user",
            email="user2@example.com",
            hashed_password=hash_password("pass123")
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):
            test_db.commit()


class TestTranscriptionJobModel:
    """Test TranscriptionJob model."""
    
    def test_create_job(self, test_db):
        """Test job creation."""
        job = TranscriptionJob(
            id=str(uuid4()),
            user_id=str(uuid4()),
            filename="test.wav",
            original_filename="test.wav",
            file_size_bytes=1000000,
            file_path="/storage/test.wav",
            status="pending"
        )
        test_db.add(job)
        test_db.commit()
        
        db_job = test_db.query(TranscriptionJob).filter(TranscriptionJob.filename == "test.wav").first()
        assert db_job is not None
        assert db_job.status == "pending"
        assert db_job.file_size_bytes == 1000000
    
    def test_update_job(self, test_db):
        """Test job update."""
        job_id = str(uuid4())
        job = TranscriptionJob(
            id=job_id,
            user_id=str(uuid4()),
            filename="test.wav",
            original_filename="test.wav",
            file_size_bytes=1000000,
            file_path="/storage/test.wav",
            status="pending"
        )
        test_db.add(job)
        test_db.commit()
        
        # Update job
        db_job = test_db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
        db_job.status = "completed"
        db_job.transcript_text = "Sample transcript"
        test_db.commit()
        
        updated_job = test_db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
        assert updated_job.status == "completed"
        assert updated_job.transcript_text == "Sample transcript"


class TestAuditLogModel:
    """Test AuditLog model."""
    
    def test_create_audit_log(self, test_db):
        """Test audit log creation."""
        log = AuditLog(
            id=str(uuid4()),
            user_id=str(uuid4()),
            action="login",
            ip_address="192.168.1.1",
            status="success"
        )
        test_db.add(log)
        test_db.commit()
        
        db_log = test_db.query(AuditLog).filter(AuditLog.action == "login").first()
        assert db_log is not None
        assert db_log.status == "success"
