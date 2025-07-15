#!/usr/bin/env python3
"""Create admin user using direct SQL"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from admin.core.security import hash_password
from database.database import engine
from sqlalchemy import text

def create_admin_user():
    """Create admin user with direct SQL"""
    
    username = "admin"
    email = "admin@example.com"
    password = "Admin123!"
    hashed_password = hash_password(password)
    
    with engine.connect() as conn:
        # Check if user exists
        result = conn.execute(text("""
            SELECT id FROM admin_users 
            WHERE username = :username OR email = :email
        """), {"username": username, "email": email})
        
        if result.first():
            print(f"✅ Admin user '{username}' already exists")
            return
        
        # Create user
        conn.execute(text("""
            INSERT INTO admin_users (username, email, hashed_password, role, is_active, full_name)
            VALUES (:username, :email, :hashed_password, :role, :is_active, :full_name)
        """), {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role": "super_admin",
            "is_active": True,
            "full_name": "System Administrator"
        })
        
        conn.commit()
        
        print(f"✅ Created admin user '{username}' with email '{email}'")
        print(f"🔑 Password: {password}")
        print(f"🌐 Access at: http://localhost:8000/login")

if __name__ == "__main__":
    create_admin_user()