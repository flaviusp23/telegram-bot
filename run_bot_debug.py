#!/usr/bin/env python3
"""Debug version of bot runner with extra logging."""
import logging
import os

# Set up detailed logging BEFORE any imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

logger.info("=== BOT DEBUG STARTUP ===")
logger.info(f"Python version: {os.sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'Not set')}")

# Log all environment variables (hiding sensitive values)
logger.info("Environment variables:")
for key, value in os.environ.items():
    if any(sensitive in key.upper() for sensitive in ['TOKEN', 'KEY', 'PASSWORD', 'SECRET']):
        logger.info(f"  {key}: ***hidden*** (length: {len(value)})")
    else:
        logger.info(f"  {key}: {value}")

try:
    logger.info("Importing bot.main...")
    from bot.main import main
    
    logger.info("Starting bot main()...")
    main()
    
except Exception as e:
    logger.error(f"Failed to start bot: {e}", exc_info=True)