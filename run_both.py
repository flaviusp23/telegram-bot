#!/usr/bin/env python3
"""Run both bot and admin panel in separate processes."""
import asyncio
import logging
import multiprocessing
import os
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_bot():
    """Run the Telegram bot."""
    logger.info("Starting Telegram bot...")
    os.system("python run_bot.py")


def run_admin():
    """Run the admin panel."""
    logger.info("Starting admin panel...")
    # Wait a bit for bot to start first
    time.sleep(5)
    os.system("python run_admin.py --host 0.0.0.0 --port $PORT")


if __name__ == "__main__":
    logger.info("Starting both bot and admin services...")
    
    # Start bot in separate process
    bot_process = multiprocessing.Process(target=run_bot)
    bot_process.start()
    
    # Start admin in main process (so Railway can access the web port)
    run_admin()
    
    # Clean up
    bot_process.terminate()
    bot_process.join()