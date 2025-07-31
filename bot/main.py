"""Main Telegram bot with integrated scheduler for diabetes monitoring system.

This is the main entry point for the bot. It sets up:
- Application and handlers
- Scheduler for automatic questionnaires
- Error handling
- Logging

Naming conventions:
- Variables: snake_case
  - user (consistent naming for user objects)
  - telegram_id (not telegramId)
  - response_value, question_type (descriptive names)
- Functions: snake_case with descriptive action verbs
- Constants: Imported from config modules using PascalCase classes
- Async functions: Prefixed with action verb (send_, handle_, etc.)
"""
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import BOT_TOKEN, ENVIRONMENT, IS_DEVELOPMENT
from bot_config.bot_constants import (
    AlertSettings, BotSettings, BotMessages, LogMessages
)
from database.models import User
from bot.decorators import (
    require_registered_user, admin_only, log_command_usage
)
from bot.scheduler import send_scheduled_alerts
from bot.handlers import (
    start, register, status, pause_alerts, resume_alerts,
    questionnaire, questionnaire_dds2, button_callback, button_callback_dds2, export_data
)

# Enable logging
logging.basicConfig(
    format=BotSettings.LOG_FORMAT,
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


# Command handlers that remain in main.py
@log_command_usage
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(BotMessages.HELP_TEXT)


@log_command_usage
async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Health check for monitoring"""
    scheduler_status = "running" if scheduler.running else "stopped"
    jobs = scheduler.get_jobs()
    
    health_msg = BotMessages.HEALTH_STATUS_TEMPLATE.format(
        scheduler_status=scheduler_status,
        environment=ENVIRONMENT,
        job_count=len(jobs)
    )
    
    if IS_DEVELOPMENT:
        health_msg += BotMessages.HEALTH_DEV_MODE.format(minutes=AlertSettings.DEV_ALERT_INTERVAL_MINUTES)
    else:
        health_msg += BotMessages.HEALTH_PROD_MODE
    
    await update.message.reply_text(health_msg)


@require_registered_user
@admin_only()
@log_command_usage
async def send_alerts_now(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Manually trigger alerts to all active users"""
    await update.message.reply_text(BotMessages.SEND_ALERTS_START)
    await send_scheduled_alerts(context.bot)
    await update.message.reply_text(BotMessages.SEND_ALERTS_COMPLETE)


# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors"""
    logger.error(LogMessages.ERROR_UPDATE.format(update=update, error=context.error))


async def post_init(application: Application) -> None:
    """Initialize the bot and scheduler after startup"""
    bot = application.bot
    logger.info(LogMessages.BOT_INITIALIZING.format(environment=ENVIRONMENT))
    
    # Schedule alerts based on environment
    if IS_DEVELOPMENT:
        # Development mode: run every N minutes
        scheduler.add_job(
            send_scheduled_alerts,
            'interval',
            minutes=AlertSettings.DEV_ALERT_INTERVAL_MINUTES,
            args=[bot],
            id=BotSettings.DEV_ALERT_JOB_ID,
            replace_existing=True,
            coalesce=BotSettings.SCHEDULER_COALESCE,
            max_instances=BotSettings.SCHEDULER_MAX_INSTANCES
        )
        logger.info(LogMessages.SCHEDULER_DEV_MODE.format(minutes=AlertSettings.DEV_ALERT_INTERVAL_MINUTES))
    else:
        # Production mode: schedule at specific times
        for idx, time_config in enumerate(AlertSettings.PROD_ALERT_TIMES):
            scheduler.add_job(
                send_scheduled_alerts,
                'cron',
                hour=time_config['hour'],
                minute=time_config['minute'],
                args=[bot],
                id=f'{BotSettings.PROD_ALERT_JOB_PREFIX}{idx}',
                replace_existing=True,
                coalesce=BotSettings.SCHEDULER_COALESCE,
                max_instances=BotSettings.SCHEDULER_MAX_INSTANCES
            )
        logger.info(LogMessages.SCHEDULER_PROD_MODE)
    
    # Start scheduler
    scheduler.start()
    logger.info(LogMessages.SCHEDULER_STARTED)


async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown"""
    logger.info(LogMessages.SCHEDULER_STOPPING)
    scheduler.shutdown()
    logger.info(LogMessages.SCHEDULER_STOPPED)


def main() -> None:
    """Start the bot with integrated scheduler"""
    # Create the Application with post_init and post_shutdown callbacks
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .job_queue(None)  # Disable job queue due to Python 3.13 compatibility
        .build()
    )
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("pause", pause_alerts))
    application.add_handler(CommandHandler("resume", resume_alerts))
    # Use DDS-2 questionnaire as the default
    application.add_handler(CommandHandler("questionnaire", questionnaire_dds2))
    application.add_handler(CommandHandler("export", export_data))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CommandHandler("send_now", send_alerts_now))
    
    # Register callback query handlers - DDS-2 first, then legacy
    async def combined_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callbacks, trying DDS-2 first, then legacy"""
        # Try DDS-2 handler first
        handled = await button_callback_dds2(update, context)
        if not handled:
            # Fall back to legacy handler
            await button_callback(update, context)
    
    application.add_handler(CallbackQueryHandler(combined_button_callback))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info(LogMessages.BOT_STARTING)
    logger.info(LogMessages.BOT_ENVIRONMENT.format(environment=ENVIRONMENT))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()