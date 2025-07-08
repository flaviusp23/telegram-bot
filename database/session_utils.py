"""Database session management utilities for eliminating code duplication"""
import logging
from functools import wraps
from contextlib import contextmanager
from typing import TypeVar, Callable, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.database import SessionLocal

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic function return types
T = TypeVar('T')


@contextmanager
def db_session_context(commit: bool = True, rollback_on_error: bool = True) -> Session:
    """
    Context manager for database sessions with automatic cleanup and error handling.
    
    Args:
        commit: Whether to commit the transaction on successful completion (default: True)
        rollback_on_error: Whether to rollback on exceptions (default: True)
    
    Yields:
        Session: Database session object
    
    Example:
        with db_session_context() as db:
            user = db.query(User).filter(User.id == 1).first()
            user.name = "New Name"
            # Automatically commits and closes
    """
    db = SessionLocal()
    try:
        logger.debug("Opening database session")
        yield db
        if commit:
            db.commit()
            logger.debug("Database transaction committed")
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        if rollback_on_error:
            db.rollback()
            logger.debug("Database transaction rolled back")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database operation: {e}")
        if rollback_on_error:
            db.rollback()
            logger.debug("Database transaction rolled back")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def with_db_session(commit: bool = True, rollback_on_error: bool = True) -> Callable:
    """
    Decorator that provides a database session to the decorated function.
    
    Args:
        commit: Whether to commit the transaction on successful completion (default: True)
        rollback_on_error: Whether to rollback on exceptions (default: True)
    
    Returns:
        Decorated function with database session as first argument
    
    Example:
        @with_db_session()
        def update_user(db: Session, user_id: int, name: str):
            user = db.query(User).filter(User.id == user_id).first()
            user.name = name
            # Automatically commits
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with db_session_context(commit=commit, rollback_on_error=rollback_on_error) as db:
                return func(db, *args, **kwargs)
        return wrapper
    return decorator


def get_db_for_request() -> Session:
    """
    Get a database session for use in request handlers.
    
    Returns:
        Session: Database session object
    
    Note:
        This is a simple session getter for cases where context managers
        or decorators aren't suitable. Remember to close the session manually.
    """
    return SessionLocal()