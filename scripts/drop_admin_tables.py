#!/usr/bin/env python3
"""Drop admin tables if they exist - for clean migration"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.database import engine
from sqlalchemy import text

def drop_admin_tables():
    """Drop admin tables if they exist"""
    with engine.connect() as conn:
        # Drop tables in correct order (foreign keys first)
        conn.execute(text("DROP TABLE IF EXISTS admin_sessions"))
        conn.execute(text("DROP TABLE IF EXISTS audit_logs"))
        conn.execute(text("DROP TABLE IF EXISTS admin_users"))
        conn.commit()
        print("Admin tables dropped successfully")

if __name__ == "__main__":
    drop_admin_tables()