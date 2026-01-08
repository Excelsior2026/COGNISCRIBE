"""Database transaction management utilities."""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from src.database.config import SessionLocal
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@contextmanager
def db_transaction() -> Generator[Session, None, None]:
    """Context manager for database transactions with automatic rollback on error.
    
    Usage:
        with db_transaction() as db:
            user = User(...)
            db.add(user)
            # Transaction commits automatically on success
            # Rolls back automatically on exception
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction rolled back: {str(e)}")
        raise
    finally:
        db.close()
