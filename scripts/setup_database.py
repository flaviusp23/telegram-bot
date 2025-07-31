#!/usr/bin/env python3
"""Database setup script for the diabetes monitoring system.

This script handles:
- Creating the database if it doesn't exist
- Running Alembic migrations
- Creating tables directly (fallback option)
"""
from pathlib import Path
import subprocess
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.database import create_database_if_not_exists, test_connection, init_database


def run_migrations():
    """Run Alembic migrations."""
    try:
        print("\nRunning database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Alembic not found. Please install it with: pip install alembic")
        return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False


def setup_database(create_tables=False):
    """Set up the database.
    
    Args:
        create_tables: If True, create tables directly instead of using migrations
    """
    print("Setting up database...")
    
    # Step 1: Create database if it doesn't exist
    if not create_database_if_not_exists():
        print("❌ Failed to create database")
        sys.exit(1)
    
    # Step 2: Test connection
    if not test_connection():
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    # Step 3: Create tables
    if create_tables:
        # Direct table creation
        if init_database():
            print("✅ Database setup complete!")
        else:
            print("❌ Failed to create tables")
            sys.exit(1)
    else:
        # Use migrations
        if run_migrations():
            print("✅ Database setup complete!")
        else:
            print("\n⚠️  Migration failed. You can try:")
            print("   1. Fix the migration issue and run this script again")
            print("   2. Run with --create-tables flag to create tables directly")
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-tables":
        print("\nCreating tables directly...")
        setup_database(create_tables=True)
    else:
        print("\nUsing Alembic migrations...")
        setup_database(create_tables=False)