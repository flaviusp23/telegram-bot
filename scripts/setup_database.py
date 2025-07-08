import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.database import create_database_if_not_exists, test_connection, init_db

def setup_database(create_tables=False):
    """Complete database setup using SQLAlchemy"""
    
    print("=== Database Setup ===\n")
    
    # Step 1: Create database if needed
    print("1. Creating database...")
    if not create_database_if_not_exists():
        print("Failed to create database. Check your MySQL connection.")
        return False
    
    # Step 2: Test connection
    print("\n2. Testing connection...")
    if not test_connection():
        print("Failed to connect to database.")
        return False
    
    # Step 3: Optionally create tables
    if create_tables:
        print("\n3. Creating tables...")
        if not init_db():
            print("Failed to create tables.")
            return False
    
    print("\n=== Setup Complete ===")
    return True

if __name__ == "__main__":
    if setup_database():
        print("\nNext steps:")
        print("1. Run: source venv/bin/activate")
        print("2. Run: alembic revision --autogenerate -m 'Initial tables'")
        print("3. Run: alembic upgrade head")
        print("\nOr to create tables directly without Alembic:")
        print("Run: python scripts/setup_database.py --create-tables")
        
        # Check if user wants to create tables directly
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "--create-tables":
            print("\nCreating tables directly...")
            setup_database(create_tables=True)