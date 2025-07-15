#!/usr/bin/env python3
"""
Script to create the first superadmin user for the admin panel.

This script prompts for username, email, and password, validates the inputs,
and creates the first superadmin user in the database.
"""

import sys
import os
import getpass
import re
from datetime import datetime

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.database import SessionLocal, engine, create_database_if_not_exists, test_connection
from admin.models.admin import AdminUser, AdminRole, Base
from admin.core.security import hash_password, validate_password_strength


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """Validate username format."""
    # Username must be 3-50 characters, alphanumeric with underscores
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return re.match(pattern, username) is not None


def check_existing_admin(db: Session) -> bool:
    """Check if any admin users already exist."""
    count = db.query(AdminUser).count()
    return count > 0


def get_user_input():
    """Get and validate user input for creating admin user."""
    print("\n" + "="*60)
    print("CREATE FIRST SUPERADMIN USER")
    print("="*60 + "\n")
    
    # Get username
    while True:
        username = input("Enter username (3-50 characters, alphanumeric + underscore): ").strip()
        if not username:
            print("❌ Username cannot be empty.")
            continue
        if not validate_username(username):
            print("❌ Invalid username. Must be 3-50 characters, alphanumeric with underscores only.")
            continue
        break
    
    # Get email
    while True:
        email = input("Enter email address: ").strip().lower()
        if not email:
            print("❌ Email cannot be empty.")
            continue
        if not validate_email(email):
            print("❌ Invalid email format.")
            continue
        break
    
    # Get password
    print("\nPassword requirements:")
    print("- Minimum 8 characters")
    print("- At least one uppercase letter")
    print("- At least one lowercase letter")
    print("- At least one digit")
    print("- At least one special character")
    
    while True:
        password = getpass.getpass("\nEnter password: ")
        if not password:
            print("❌ Password cannot be empty.")
            continue
        
        # Validate password strength
        validation_result = validate_password_strength(password)
        if not validation_result["valid"]:
            print(f"❌ {validation_result['message']}")
            continue
        
        # Confirm password
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match.")
            continue
        
        print("✅ Password validated successfully.")
        break
    
    return username, email, password


def create_admin_user(username: str, email: str, password: str) -> bool:
    """Create the superadmin user in the database."""
    db = SessionLocal()
    try:
        # Check if any admin users exist
        if check_existing_admin(db):
            print("\n⚠️  WARNING: Admin users already exist in the database.")
            response = input("Do you still want to create a new superadmin? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Operation cancelled.")
                return False
        
        # Create the admin user
        admin_user = AdminUser(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=AdminRole.superadmin,
            is_active=True,
            created_at=datetime.utcnow(),
            failed_login_attempts=0
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"\n✅ Superadmin user '{username}' created successfully!")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role.value}")
        
        return True
        
    except IntegrityError as e:
        db.rollback()
        if "username" in str(e):
            print(f"\n❌ Error: Username '{username}' already exists.")
        elif "email" in str(e):
            print(f"\n❌ Error: Email '{email}' already exists.")
        else:
            print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        db.rollback()
        print(f"\n❌ Unexpected error: {e}")
        return False
    finally:
        db.close()


def main():
    """Main function to run the script."""
    try:
        print("\n🚀 Admin User Creation Script")
        print("This script will create the first superadmin user for the admin panel.\n")
        
        # Ensure database exists and is connected
        print("Checking database connection...")
        
        if not create_database_if_not_exists():
            print("❌ Failed to create/connect to database.")
            sys.exit(1)
        
        if not test_connection():
            print("❌ Failed to connect to database.")
            sys.exit(1)
        
        # Create tables if they don't exist
        print("Ensuring admin tables exist...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database ready.\n")
        
        # Get user input
        username, email, password = get_user_input()
        
        # Confirm creation
        print("\n" + "-"*60)
        print("CONFIRM USER CREATION:")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Role: superadmin")
        print("-"*60)
        
        confirm = input("\nCreate this user? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
        
        # Create the user
        if create_admin_user(username, email, password):
            print("\n" + "="*60)
            print("🎉 SUCCESS! Your superadmin user has been created.")
            print("\nLogin Instructions:")
            print(f"1. Navigate to the admin panel (usually at /admin or /admin/login)")
            print(f"2. Username: {username}")
            print(f"3. Password: [the password you just entered]")
            print("\nYou can now use this superadmin account to:")
            print("- Access the admin dashboard")
            print("- Create additional admin users")
            print("- Manage application data")
            print("- View audit logs")
            print("="*60 + "\n")
        else:
            print("\n❌ Failed to create admin user.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()