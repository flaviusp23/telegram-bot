#!/usr/bin/env python3
"""Railway-specific startup script."""
import os
import sys

# Get port from Railway environment
port = os.getenv('PORT', '8080')
print(f"Starting admin panel on port {port}")

# Run admin panel
os.execv(sys.executable, [
    sys.executable, 
    'run_admin.py', 
    '--host', '0.0.0.0', 
    '--port', port,
    '--no-reload'
])