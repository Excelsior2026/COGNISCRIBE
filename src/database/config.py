"""Database configuration and connection management."""
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
import os
from typing import Generator

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Set it to your database connection string (e.g., postgresql://user:password@host:port/database)"
    )

# SQLAlchemy engine configuration
def get_engine():
    """Create SQLAlchemy engine with proper pooling."""
    if "sqlite" in DATABASE_URL:
        # SQLite configuration (development/testing)
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # PostgreSQL configuration (production)
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,
        )
    return engine


# Session factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from src.database.models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized")


def drop_db():
    """Drop all database tables (WARNING: destructive)."""
    from src.database.models import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")
