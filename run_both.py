#!/usr/bin/env python3
"""Run both bot and admin panel in separate processes."""
import asyncio
import logging
import multiprocessing
import os
import sys
import time
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_bot():
    """Run the Telegram bot."""
    logger.info("Starting Telegram bot...")
    subprocess.run([sys.executable, "run_bot.py"])


def run_admin():
    """Run the admin panel."""
    logger.info("Starting admin panel...")
    # Wait a bit for bot to start first
    time.sleep(3)
    port = os.getenv('PORT', '8000')
    subprocess.run([sys.executable, "run_admin.py", "--host", "0.0.0.0", "--port", port])


if __name__ == "__main__":
    logger.info("Starting both bot and admin services...")
    
    try:
        # Start bot in separate process
        bot_process = multiprocessing.Process(target=run_bot)
        bot_process.start()
        logger.info(f"Bot process started with PID: {bot_process.pid}")
        
        # Start admin in main process (so Railway can access the web port)
        run_admin()
        
    except KeyboardInterrupt:
        logger.info("Shutting down services...")
    finally:
        # Clean up
        if 'bot_process' in locals():
            bot_process.terminate()
            bot_process.join()
            logger.info("Services stopped")