#!/usr/bin/env python3
"""Run all pending Alembic migrations."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from database.database import SQLALCHEMY_DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_database_connection():
    """Check if database is accessible."""
    logger.info("Checking database connection...")
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def run_migrations():
    """Run all pending Alembic migrations."""
    logger.info("Running database migrations...")
    
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Set the database URL in alembic config
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    
    try:
        # Get current revision
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            logger.info(f"Current database revision: {current_rev}")
        
        # Run migrations to latest version
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully")
        
        # Get new revision
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            new_rev = context.get_current_revision()
            logger.info(f"New database revision: {new_rev}")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def main():
    """Main migration runner."""
    logger.info("Starting migration runner...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database. Exiting...")
        sys.exit(1)
    
    try:
        # Run migrations
        run_migrations()
        logger.info("All migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()