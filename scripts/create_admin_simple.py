#!/usr/bin/env python3
"""Simple admin user creation script"""

from pathlib import Path
import os
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from admin.core.security import hash_password
from admin.models.admin import AdminUser, AdminRole
from database.database import SessionLocal


def create_admin_user():
    """Create an admin user with credentials from environment variables."""
    # Get admin credentials from environment or use defaults
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(AdminUser).filter(
            (AdminUser.username == username) | 
            (AdminUser.email == email)
        ).first()
        
        if existing:
            print(f"✅ Admin user '{username}' already exists")
            return
        
        # Create user
        admin_user = AdminUser(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=AdminRole.super_admin,
            is_active=True,
            full_name="System Administrator"
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ Created admin user '{username}' with email '{email}'")
        print(f"🔑 Password: {password}")
        print(f"🌐 Login at your Railway app URL + /login")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()