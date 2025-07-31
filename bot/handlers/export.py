"""Export data handlers for the diabetes monitoring bot.

Handles:
- /export command
- Helper functions for data export
"""
from datetime import datetime, timedelta
import logging
import os
import shutil

from telegram import Update
from telegram.ext import ContextTypes

from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    log_command_usage,
    rate_limit
)
from bot_config.bot_constants import (
    BotMessages, ExportSettings, LogMessages
)
from database import db_session_context
from database.models import User, Response
from scripts.data_export_dds2 import DDS2DataExporter

logger = logging.getLogger(__name__)


def cleanup_export_dir(export_dir: str) -> None:
    """Clean up temporary export directory"""
    try:
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
            logger.info(f"Cleaned up export directory: {export_dir}")
    except Exception as e:
        logger.error(f"Failed to cleanup export directory {export_dir}: {e}")


@require_registered_user
@update_last_interaction
@rate_limit(max_calls=2, period_seconds=300)  # Allow 2 exports per 5 minutes
@log_command_usage
async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Export user data and send files via Telegram - orchestrator function"""
    telegram_id = user.telegram_id
    export_dir = None
    
    await update.message.reply_text(BotMessages.EXPORT_GENERATING)
    
    # Set date range (last N days by default)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=ExportSettings.DEFAULT_EXPORT_DAYS)
    
    try:
        # Step 1: Prepare export directory
        export_dir = prepare_export_directory(telegram_id)
        
        # Step 2: Generate export files (XML and graphs)
        with db_session_context(commit=False) as db:
            export_results = generate_export_files(
                db=db,
                user=user,
                start_date=start_date,
                end_date=end_date,
                export_dir=export_dir
            )
        
        # Step 3: Send files to user
        await send_export_files_to_user(
            update=update,
            export_dir=export_dir,
            stats=export_results['stats'],
            graphs_generated=export_results['graphs_generated']
        )
        
        await update.message.reply_text(BotMessages.EXPORT_COMPLETE)
        
    except Exception as e:
        logger.error(LogMessages.ERROR_EXPORT.format(error=e))
        await update.message.reply_text(BotMessages.ERROR_EXPORT)
    finally:
        # Step 4: Clean up temporary files
        if export_dir:
            cleanup_export_directory(export_dir)