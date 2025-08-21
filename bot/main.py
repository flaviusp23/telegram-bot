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
import warnings

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from bot.decorators import (
    require_registered_user, admin_only, log_command_usage
)
from bot.handlers import (
    start, register, status, pause_alerts, resume_alerts,
    questionnaire_dds2, button_callback_dds2, export_data
)
from bot.handlers.auth import initial_language_callback
from bot.handlers.language import language_command, language_callback
from bot.handlers.emotional_support import (
    start_support, handle_support_message, cancel_support, CHATTING,
    support_callback
)
from bot.scheduler import send_scheduled_alerts
from bot_config.bot_constants import (
    AlertSettings, BotSettings, BotMessages, LogMessages
)
from config import BOT_TOKEN, ENVIRONMENT, IS_DEVELOPMENT
from database.models import User

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    from bot.handlers.language import get_user_language, get_message
    from database import db_session_context, get_user_by_telegram_id
    
    telegram_id = str(update.effective_user.id)
    with db_session_context(commit=False) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        lang = get_user_language(context, user)
    
    help_text = get_message('HELP_TEXT', lang)
    await update.message.reply_text(help_text)


@log_command_usage
async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Health check for monitoring"""
    from bot.handlers.language import get_user_language, get_message
    from database import db_session_context, get_user_by_telegram_id
    from bot.llm_service import get_llm_service
    
    telegram_id = str(update.effective_user.id)
    with db_session_context(commit=False) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        lang = get_user_language(context, user)
    
    scheduler_status = "running" if scheduler.running else "stopped"
    jobs = scheduler.get_jobs()
    
    # Check Gemini/LLM status
    llm_service = get_llm_service()
    gemini_available = await llm_service.is_available()
    gemini_status = "✅ Available" if gemini_available else "❌ Not Available"
    
    health_msg = get_message('HEALTH_STATUS_TEMPLATE', lang).format(
        scheduler_status=scheduler_status,
        environment=ENVIRONMENT,
        job_count=len(jobs)
    )
    
    # Add Gemini status to health message
    health_msg += f"\n🤖 Gemini AI: {gemini_status}"
    
    if IS_DEVELOPMENT:
        health_msg += get_message('HEALTH_DEV_MODE', lang).format(minutes=AlertSettings.DEV_ALERT_INTERVAL_MINUTES)
    else:
        health_msg += get_message('HEALTH_PROD_MODE', lang)
    
    await update.message.reply_text(health_msg)


@require_registered_user
@admin_only()
@log_command_usage
async def send_alerts_now(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Manually trigger alerts to all active users"""
    from bot.handlers.language import get_user_language, get_message
    
    lang = get_user_language(context, user)
    
    await update.message.reply_text(get_message('SEND_ALERTS_START', lang))
    await send_scheduled_alerts(context.bot)
    await update.message.reply_text(get_message('SEND_ALERTS_COMPLETE', lang))


@log_command_usage
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /done command - simple acknowledgment"""
    from bot.handlers.language import get_user_language
    from database import db_session_context, get_user_by_telegram_id
    
    telegram_id = str(update.effective_user.id)
    with db_session_context(commit=False) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        lang = get_user_language(context, user)
    
    # Send acknowledgment based on language
    if lang == 'es':
        message = "✅ ¡Hecho! Comando recibido."
    elif lang == 'ro':
        message = "✅ Gata! Comandă primită."
    else:
        message = "✅ Done! Command received."
    
    await update.message.reply_text(message)


# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors"""
    logger.error(LogMessages.ERROR_UPDATE.format(update=update, error=context.error))


async def setup_bot_commands(application: Application) -> None:
    """Set up bot commands for autocomplete in all languages"""
    # Define commands with descriptions for each language
    commands_en = [
        BotCommand("start", "Start the bot"),
        BotCommand("register", "Register as a new user"),
        BotCommand("help", "Show help message"),
        BotCommand("status", "Check your registration status"),
        BotCommand("language", "Change language preference"),
        BotCommand("pause", "Pause automatic questionnaires"),
        BotCommand("resume", "Resume automatic questionnaires"),
        BotCommand("questionnaire", "Complete diabetes distress questionnaire"),
        BotCommand("support", "Chat with AI emotional support"),
        BotCommand("export", "Export your data (XML + graphs)"),
        BotCommand("health", "Check bot health status"),
        BotCommand("done", "End current conversation")
    ]
    
    commands_es = [
        BotCommand("start", "Iniciar el bot"),
        BotCommand("register", "Registrarse como nuevo usuario"),
        BotCommand("help", "Mostrar mensaje de ayuda"),
        BotCommand("status", "Verificar estado de registro"),
        BotCommand("language", "Cambiar idioma"),
        BotCommand("pause", "Pausar cuestionarios automáticos"),
        BotCommand("resume", "Reanudar cuestionarios automáticos"),
        BotCommand("questionnaire", "Completar cuestionario de estrés"),
        BotCommand("support", "Chatear con asistente IA"),
        BotCommand("export", "Exportar tus datos (XML + gráficos)"),
        BotCommand("health", "Verificar estado del bot"),
        BotCommand("done", "Terminar conversación actual")
    ]
    
    commands_ro = [
        BotCommand("start", "Pornește bot-ul"),
        BotCommand("register", "Înregistrează-te ca utilizator nou"),
        BotCommand("help", "Afișează mesajul de ajutor"),
        BotCommand("status", "Verifică starea înregistrării"),
        BotCommand("language", "Schimbă limba"),
        BotCommand("pause", "Întrerupe chestionarele automate"),
        BotCommand("resume", "Reia chestionarele automate"),
        BotCommand("questionnaire", "Completează chestionarul de stres"),
        BotCommand("support", "Discută cu asistentul AI"),
        BotCommand("export", "Exportă datele tale (XML + grafice)"),
        BotCommand("health", "Verifică starea bot-ului"),
        BotCommand("done", "Încheie conversația curentă")
    ]
    
    # Add admin command if in development
    if IS_DEVELOPMENT:
        commands_en.append(BotCommand("send_now", "Send alerts now (admin)"))
        commands_es.append(BotCommand("send_now", "Enviar alertas ahora (admin)"))
        commands_ro.append(BotCommand("send_now", "Trimite alerte acum (admin)"))
    
    # Set commands for each language
    await application.bot.set_my_commands(commands_en, language_code="en")
    await application.bot.set_my_commands(commands_es, language_code="es")
    await application.bot.set_my_commands(commands_ro, language_code="ro")
    
    # Set default commands (English)
    await application.bot.set_my_commands(commands_en)
    
    logger.info("Bot commands configured for all languages")


async def post_init(application: Application) -> None:
    """Initialize the bot and scheduler after startup"""
    bot = application.bot
    logger.info(LogMessages.BOT_INITIALIZING.format(environment=ENVIRONMENT))
    
    # Set up bot commands for autocomplete
    await setup_bot_commands(application)
    
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
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("pause", pause_alerts))
    application.add_handler(CommandHandler("resume", resume_alerts))
    # Use DDS-2 questionnaire as the default
    application.add_handler(CommandHandler("questionnaire", questionnaire_dds2))
    application.add_handler(CommandHandler("export", export_data))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CommandHandler("send_now", send_alerts_now))
    application.add_handler(CommandHandler("done", done_command))
    
    # Register callback query handlers
    application.add_handler(CallbackQueryHandler(button_callback_dds2, pattern="^dds2_"))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^set_language_"))
    application.add_handler(CallbackQueryHandler(initial_language_callback, pattern="^initial_language_"))
    
    # Add emotional support conversation handler
    support_handler = ConversationHandler(
        entry_points=[
            CommandHandler("support", start_support),
            CallbackQueryHandler(support_callback, pattern="^(start_support|decline_support)$")
        ],
        states={
            CHATTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message)]
        },
        fallbacks=[CommandHandler("cancel", cancel_support)],
        per_chat=True,
        per_user=True
    )
    application.add_handler(support_handler)
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info(LogMessages.BOT_STARTING)
    logger.info(LogMessages.BOT_ENVIRONMENT.format(environment=ENVIRONMENT))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()