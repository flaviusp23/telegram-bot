#!/usr/bin/env python3
"""Test bot startup and configuration."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import logging
import asyncio
from telegram import Bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bot():
    """Test bot connection and configuration."""
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set!")
        return False
    
    logger.info(f"Bot token found (length: {len(bot_token)})")
    
    try:
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        logger.info(f"✅ Bot connected successfully!")
        logger.info(f"Bot username: @{me.username}")
        logger.info(f"Bot name: {me.first_name}")
        logger.info(f"Bot ID: {me.id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect bot: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Testing bot startup...")
    
    # Test environment variables
    env_vars = ['BOT_TOKEN', 'DATABASE_URL', 'GOOGLE_API_KEY', 'ENCRYPTION_KEY']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var} is set (length: {len(value)})")
        else:
            logger.warning(f"❌ {var} is NOT set")
    
    # Check for ALL environment variables that might be database-related
    logger.info("\nAll environment variables containing 'SQL', 'DB', or 'DATABASE':")
    for key, value in os.environ.items():
        if any(word in key.upper() for word in ['SQL', 'DB', 'DATABASE']):
            if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'PASS', 'KEY', 'SECRET']):
                logger.info(f"  {key} = ***hidden*** (length: {len(value)})")
            else:
                logger.info(f"  {key} = {value}")
    
    # Test database connection attempt
    logger.info("\nTesting database connection...")
    try:
        from database.database import SQLALCHEMY_DATABASE_URL
        logger.info(f"Database URL constructed: {SQLALCHEMY_DATABASE_URL[:50]}...")
        
        from sqlalchemy import create_engine, text
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("✅ Database connection successful!")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    # Test bot connection
    success = await test_bot()
    
    if success:
        logger.info("✅ All tests passed! Bot should be able to start.")
    else:
        logger.error("❌ Tests failed. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())