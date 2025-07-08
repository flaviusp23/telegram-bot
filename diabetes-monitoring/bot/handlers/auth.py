"""Authentication and registration handlers for the diabetes monitoring bot.

Handles:
- /start command
- /register command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    create_user,
    db_session_context
)
from database.models import User
from database.constants import DefaultValues
from bot_config.bot_constants import BotMessages, LogMessages
from bot.decorators import (
    with_user_context,
    log_command_usage
)

logger = logging.getLogger(__name__)


@with_user_context
@log_command_usage
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None) -> None:
    """Send a message when the command /start is issued."""
    telegram_user = update.effective_user
    
    if user:
        # User is already registered
        await update.message.reply_text(
            BotMessages.WELCOME_BACK.format(first_name=user.first_name)
        )
    else:
        # New user
        await update.message.reply_text(
            BotMessages.WELCOME_NEW.format(first_name=telegram_user.first_name)
        )


@with_user_context
@log_command_usage
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None) -> None:
    """Register a new user"""
    telegram_user = update.effective_user
    telegram_id = str(telegram_user.id)
    
    try:
        with db_session_context() as db:
            # Check if already registered
            if user:
                await update.message.reply_text(
                    BotMessages.ALREADY_REGISTERED.format(first_name=user.first_name)
                )
                return
            
            # Register new user
            user = create_user(
                db=db,
                first_name=telegram_user.first_name or DefaultValues.DEFAULT_NAME,
                family_name=telegram_user.last_name or DefaultValues.DEFAULT_FAMILY_NAME,
                passport_id=None,
                phone_number=None,
                telegram_id=telegram_id,
                email=None
            )
            
            await update.message.reply_text(
                BotMessages.REGISTRATION_SUCCESS.format(first_name=user.first_name)
            )
            
    except Exception as e:
        logger.error(LogMessages.ERROR_REGISTRATION.format(error=e))
        await update.message.reply_text(BotMessages.REGISTRATION_ERROR)