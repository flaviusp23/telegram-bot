#!/usr/bin/env python3
"""Debug script to test admin panel components individually."""
import os
import sys
import traceback

print("=== ADMIN DEBUG SCRIPT ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Test environment
print("\n=== ENVIRONMENT ===")
for key, value in os.environ.items():
    if any(sensitive in key.upper() for sensitive in ['TOKEN', 'KEY', 'PASSWORD', 'SECRET']):
        print(f"{key}: ***hidden*** (length: {len(value)})")
    else:
        print(f"{key}: {value}")

print("\n=== TESTING IMPORTS ===")

try:
    print("1. Testing basic imports...")
    import logging
    import sqlalchemy
    print("✅ Basic imports OK")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")
    traceback.print_exc()

try:
    print("2. Testing database connection...")
    from database.database import SQLALCHEMY_DATABASE_URL, engine
    print(f"Database URL: {SQLALCHEMY_DATABASE_URL[:50]}...")
    
    with engine.connect() as conn:
        result = conn.execute(sqlalchemy.text("SELECT 1"))
        result.fetchone()
    print("✅ Database connection OK")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    traceback.print_exc()

try:
    print("3. Testing admin config...")
    from admin.core.config import settings
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Admin host: {settings.ADMIN_HOST}")
    print(f"Admin port: {settings.ADMIN_PORT}")
    print("✅ Admin config OK")
except Exception as e:
    print(f"❌ Admin config failed: {e}")
    traceback.print_exc()

try:
    print("4. Testing admin models...")
    from admin.models.admin import AdminUser, AdminRole
    print("✅ Admin models OK")
except Exception as e:
    print(f"❌ Admin models failed: {e}")
    traceback.print_exc()

try:
    print("5. Testing admin main...")
    import admin.main
    print("✅ Admin main import OK")
except Exception as e:
    print(f"❌ Admin main failed: {e}")
    traceback.print_exc()

try:
    print("6. Testing FastAPI app creation...")
    from admin.main import app
    print(f"App created: {type(app)}")
    print("✅ FastAPI app OK")
except Exception as e:
    print(f"❌ FastAPI app failed: {e}")
    traceback.print_exc()

print("\n=== DEBUG COMPLETE ===")