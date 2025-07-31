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
from bot.handlers.language import get_user_language, get_message
from bot_config.bot_constants import (
    BotMessages, ExportSettings, LogMessages
)
from bot_config.languages import Messages
from database import db_session_context
from database.models import User, Response
from scripts.data_export_dds2 import DDS2DataExporter

logger = logging.getLogger(__name__)


def cleanup_export_directory(export_dir: str) -> None:
    """Clean up temporary export directory"""
    try:
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
            logger.info(f"Cleaned up export directory: {export_dir}")
    except Exception as e:
        logger.error(f"Failed to cleanup export directory {export_dir}: {e}")


def prepare_export_directory(telegram_id: str) -> str:
    """Create temporary directory for export files"""
    export_dir = os.path.join(ExportSettings.EXPORT_DIR_PREFIX, f"export_{telegram_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def generate_export_files(db, user: User, start_date: datetime, end_date: datetime, export_dir: str) -> dict:
    """Generate XML and graph files for export"""
    # Get user's responses
    responses = db.query(Response).filter(
        Response.user_id == user.id,
        Response.response_timestamp >= start_date,
        Response.response_timestamp <= end_date
    ).order_by(Response.response_timestamp).all()
    
    if not responses:
        raise ValueError("No data to export")
    
    # Create exporter and generate files
    exporter = DDS2DataExporter()
    
    # Generate XML
    xml_file = exporter.export_user_data(user, responses, start_date, end_date, export_dir)
    
    # Generate graphs
    graphs_generated = False
    try:
        exporter.generate_graphs(responses, user, start_date, end_date, export_dir)
        graphs_generated = True
    except Exception as e:
        logger.warning(f"Could not generate graphs: {e}")
    
    # Calculate stats
    stats = {
        'total_responses': len(responses),
        'start_date': start_date,
        'end_date': end_date
    }
    
    return {
        'xml_file': xml_file,
        'graphs_generated': graphs_generated,
        'stats': stats
    }


async def send_export_files_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, export_dir: str, stats: dict, graphs_generated: bool, user: User):
    """Send generated export files to user via Telegram"""
    # Get user language
    user_lang = get_user_language(context, user)
    
    # Send XML file
    xml_files = [f for f in os.listdir(export_dir) if f.endswith('.xml')]
    if xml_files:
        xml_path = os.path.join(export_dir, xml_files[0])
        with open(xml_path, 'rb') as f:
            # Use translated caption
            xml_caption = get_message('EXPORT_XML_CAPTION', user_lang)
            await update.message.reply_document(
                document=f,
                filename=xml_files[0],
                caption=xml_caption
            )
    
    # Send graph images if generated
    if graphs_generated:
        image_files = sorted([f for f in os.listdir(export_dir) if f.endswith('.png')])
        for img_file in image_files:
            img_path = os.path.join(export_dir, img_file)
            with open(img_path, 'rb') as f:
                # Map file names to translation keys
                caption_map = {
                    'dds2_timeline.png': 'GRAPH_CAPTION_DDS2_SCORES',
                    'dds2_distribution.png': 'GRAPH_CAPTION_DISTRESS_DISTRIBUTION',
                    'dds2_questions.png': 'GRAPH_CAPTION_DDS2_SCORES',  # Using same key as timeline
                    'distress_timeline.png': 'GRAPH_CAPTION_DDS2_SCORES',
                    'severity_distribution.png': 'GRAPH_CAPTION_DISTRESS_DISTRIBUTION',
                    'response_rate.png': 'GRAPH_CAPTION_RESPONSE_RATE',
                    'severity_trend.png': 'GRAPH_CAPTION_DDS2_SCORES'
                }
                
                # Get translated caption or use default
                caption_key = caption_map.get(img_file)
                if caption_key:
                    caption = get_message(caption_key, user_lang)
                else:
                    # Fallback for unknown graph types
                    caption = f"📊 {img_file.replace('_', ' ').replace('.png', '').title()}"
                
                await update.message.reply_photo(
                    photo=f,
                    caption=caption
                )


@require_registered_user
@update_last_interaction
@rate_limit(max_calls=2, period_seconds=300)  # Allow 2 exports per 5 minutes
@log_command_usage
async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Export user data and send files via Telegram - orchestrator function"""
    telegram_id = user.telegram_id
    export_dir = None
    
    # Get user language
    user_lang = get_user_language(context, user)
    
    # Send generating message
    generating_msg = get_message('EXPORT_GENERATING', user_lang)
    await update.message.reply_text(generating_msg)
    
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
            context=context,
            export_dir=export_dir,
            stats=export_results['stats'],
            graphs_generated=export_results['graphs_generated'],
            user=user
        )
        
        # Send success message
        success_msg = get_message('EXPORT_SUCCESS', user_lang)
        await update.message.reply_text(success_msg)
        
    except ValueError as e:
        if "No data to export" in str(e):
            no_data_msg = get_message('EXPORT_NO_DATA', user_lang)
            await update.message.reply_text(no_data_msg)
        else:
            logger.error(LogMessages.ERROR_EXPORT.format(error=e))
            error_msg = get_message('EXPORT_ERROR', user_lang)
            await update.message.reply_text(error_msg)
    except Exception as e:
        logger.error(LogMessages.ERROR_EXPORT.format(error=e))
        error_msg = get_message('EXPORT_ERROR', user_lang)
        await update.message.reply_text(error_msg)
    finally:
        # Step 4: Clean up temporary files
        if export_dir:
            cleanup_export_directory(export_dir)