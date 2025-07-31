"""Database connection and session management.

This module handles:
- Database engine creation
- Session factory setup
- Database initialization
- Connection testing
"""
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from database.constants import DatabaseSettings

logger = logging.getLogger(__name__)

# Build database URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Create engine with connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=DatabaseSettings.POOL_SIZE,
    max_overflow=DatabaseSettings.MAX_OVERFLOW,
    pool_timeout=DatabaseSettings.POOL_TIMEOUT,
    pool_recycle=DatabaseSettings.POOL_RECYCLE,
    echo=False  # Set to True for SQL query logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Get database session.
    
    This is a dependency that will be used in FastAPI routes.
    It ensures that the database session is properly closed after use.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False


def init_database() -> bool:
    """Initialize database tables.
    
    Creates all tables defined in the models if they don't exist.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import models to ensure they're registered with Base
        from database import models  # noqa
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def create_database_if_not_exists() -> bool:
    """Create the database if it doesn't exist.
    
    Returns:
        bool: True if database exists or was created, False otherwise
    """
    # Create engine without database name
    temp_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/"
    temp_engine = create_engine(temp_url)
    
    try:
        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                {"db_name": DB_NAME}
            )
            
            if result.fetchone() is None:
                # Create database
                conn.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
                logger.info(f"Database '{DB_NAME}' created successfully")
            else:
                logger.info(f"Database '{DB_NAME}' already exists")
                
        return True
        
    except (OperationalError, ProgrammingError) as e:
        logger.error(f"Error checking/creating database: {e}")
        return False
    finally:
        temp_engine.dispose()


if __name__ == "__main__":
    # Test database connection when run directly
    if test_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")