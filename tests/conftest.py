"""Pytest configuration and shared fixtures."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.database.config import get_db
from src.api.main import app
from fastapi.testclient import TestClient

# Use SQLite for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_client(test_db_session):
    """Create test FastAPI client."""
    def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def monkeypatch_env(monkeypatch):
    """Monkeypatch environment variables for testing."""
    test_env = {
        "DATABASE_URL": TEST_SQLALCHEMY_DATABASE_URL,
        "REDIS_URL": "redis://localhost:6379/1",
        "JWT_SECRET_KEY": "test-secret-key",
        "JWT_EXPIRE_HOURS": "24",
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return monkeypatch
