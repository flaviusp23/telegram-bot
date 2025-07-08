"""Export data handlers for the diabetes monitoring bot.

Handles:
- /export command
- Helper functions for data export
"""
import logging
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from database import db_session_context
from database.models import User
from bot_config.bot_constants import (
    BotMessages, BotSettings, ExportSettings, LogMessages
)
from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    rate_limit,
    log_command_usage
)

logger = logging.getLogger(__name__)


def prepare_export_directory(telegram_id: str) -> str:
    """Creates temporary directory for export files.
    
    Args:
        telegram_id: User's telegram ID
        
    Returns:
        str: Path to the created export directory
    """
    timestamp = datetime.now().strftime(BotSettings.TIMESTAMP_FORMAT)
    export_dir = os.path.join(ExportSettings.EXPORT_DIR_PREFIX, f"user_{telegram_id}_{timestamp}")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def generate_export_files(db, user: User, start_date: datetime, end_date: datetime, export_dir: str) -> dict:
    """Generates XML export and graphs for user data.
    
    Args:
        db: Database session
        user: User object
        start_date: Start date for export
        end_date: End date for export
        export_dir: Directory to save files
        
    Returns:
        dict: Export results containing stats and graph generation status
    """
    from scripts.data_export import DataExporter
    
    # Create exporter and generate files
    exporter = DataExporter(db)
    
    # Export XML
    xml_file = os.path.join(export_dir, ExportSettings.XML_FILENAME)
    stats = exporter.export_to_xml(user.id, start_date, end_date, xml_file)
    
    # Add period information to stats for the send function
    stats['period'] = {
        'start': start_date.isoformat(),
        'end': end_date.isoformat()
    }
    
    # Generate graphs if matplotlib is available
    graphs_generated = False
    try:
        exporter.generate_graphs(user.id, start_date, end_date, export_dir)
        graphs_generated = True
    except Exception as e:
        logger.warning(LogMessages.WARNING_GRAPHS_NOT_GENERATED.format(error=e))
    
    return {
        'stats': stats,
        'xml_file': xml_file,
        'graphs_generated': graphs_generated
    }


async def send_export_files_to_user(update: Update, export_dir: str, stats: dict, graphs_generated: bool) -> None:
    """Sends export files and statistics to user via Telegram.
    
    Args:
        update: Telegram update object
        export_dir: Directory containing export files
        stats: Statistics dictionary
        graphs_generated: Whether graphs were successfully generated
    """
    timestamp = datetime.now().strftime(BotSettings.TIMESTAMP_FORMAT)
    
    # Send statistics summary
    start_date = datetime.fromisoformat(stats['period']['start'])
    end_date = datetime.fromisoformat(stats['period']['end'])
    
    summary = BotMessages.EXPORT_SUMMARY_TEMPLATE.format(
        start_date=start_date.date(),
        end_date=end_date.date(),
        total_responses=stats['total_responses'],
        distress_count=stats['distress_count'],
        distress_percentage=stats['distress_percentage'],
        average_severity=stats['average_severity'],
        response_rate=stats['response_rate']
    )
    
    # Add severity distribution details
    for level in range(1, 6):
        count = stats['severity_distribution'][level]
        if count > 0:
            summary += f"• Level {level}: {count} times\n"
    
    await update.message.reply_text(summary, parse_mode='Markdown')
    
    # Send XML file
    xml_file = os.path.join(export_dir, ExportSettings.XML_FILENAME)
    with open(xml_file, 'rb') as f:
        await update.message.reply_document(
            document=f,
            filename=f'diabetes_data_{timestamp}.xml',
            caption=BotMessages.EXPORT_XML_CAPTION
        )
    
    # Send graphs if generated
    if graphs_generated:
        graph_files = ExportSettings.GRAPHS
        
        for filename, caption in graph_files:
            filepath = os.path.join(export_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    await update.message.reply_photo(
                        photo=f,
                        caption=caption
                    )


def cleanup_export_directory(export_dir: str) -> None:
    """Cleans up temporary export directory.
    
    Args:
        export_dir: Directory to remove
    """
    import shutil
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