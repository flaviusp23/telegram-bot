#!/usr/bin/env python3
"""Railway-specific startup script."""
import os
import sys
import subprocess
import threading
import time

def run_bot():
    """Run the Telegram bot."""
    print("Starting Telegram bot...")
    subprocess.run([sys.executable, 'run_bot.py'], check=False)

def run_admin():
    """Run the admin panel."""
    port = os.getenv('PORT', '8080')
    print(f"Starting admin panel on port {port}")
    subprocess.run([
        sys.executable, 'run_admin.py', 
        '--host', '0.0.0.0', 
        '--port', port,
        '--no-reload'
    ], check=False)

if __name__ == "__main__":
    print("Starting both Telegram bot and admin panel...")
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    time.sleep(2)
    
    # Run admin panel in main thread (so Railway can access the port)
    run_admin()