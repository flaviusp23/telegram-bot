#!/usr/bin/env python3
"""Run the Telegram bot with integrated scheduler for diabetes monitoring"""
import os
import logging

# Set up logging before importing bot
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from bot.main import main

if __name__ == "__main__":
    print("Starting Diabetes Monitoring Bot with integrated scheduler...")
    
    # Log environment variable status
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        logger.info(f"✅ GOOGLE_API_KEY is set (length: {len(google_api_key)})")
    else:
        logger.error("❌ GOOGLE_API_KEY is NOT set!")
    
    # Log other critical environment variables
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token:
        logger.info("✅ BOT_TOKEN is set")
    else:
        logger.error("❌ BOT_TOKEN is NOT set!")
    
    environment = os.getenv('ENVIRONMENT', 'DEV')
    logger.info(f"📊 Environment: {environment}")
    
    main()