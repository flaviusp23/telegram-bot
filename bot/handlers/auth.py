"""Authentication and registration handlers for the diabetes monitoring bot.

Handles:
- /start command
- /register command
"""
from typing import Optional
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.decorators import (
    with_user_context,
    log_command_usage,
    update_last_interaction
)
from bot.utils.error_handling import handle_all_errors
from bot.handlers.language import get_user_language, get_message
from bot_config.bot_constants import LogMessages
from database import (
    db_session_context,
    get_user_by_telegram_id,
    create_user
)
from database.constants import DefaultValues
from database.models import User

logger = logging.getLogger(__name__)


@with_user_context
@log_command_usage
@handle_all_errors()
async def start(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    user: Optional[User] = None
) -> None:
    """Send a message when the command /start is issued.
    
    Args:
        update: Telegram update object
        context: Bot context
        user: User object if registered, None otherwise
    """
    telegram_user = update.effective_user
    
    # Get user's language preference
    lang = get_user_language(context, user)
    
    if user:
        # User is already registered
        await update.message.reply_text(
            get_message('WELCOME_BACK', lang, first_name=user.first_name)
        )
    else:
        # New user
        await update.message.reply_text(
            get_message('WELCOME_NEW', lang, first_name=telegram_user.first_name)
        )


@with_user_context
@log_command_usage
@handle_all_errors()
async def register(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    user: Optional[User] = None
) -> None:
    """Register a new user.
    
    Args:
        update: Telegram update object
        context: Bot context
        user: User object if already registered, None otherwise
    """
    telegram_user = update.effective_user
    telegram_id = str(telegram_user.id)
    
    # Get user's language preference
    lang = get_user_language(context, user)
    
    # Check if already registered
    if user:
        await update.message.reply_text(
            get_message('ALREADY_REGISTERED', lang, first_name=user.first_name)
        )
        return
    
    # Register new user
    try:
        with db_session_context() as db:
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
                get_message('REGISTRATION_SUCCESS', lang, first_name=user.first_name)
            )
    except Exception as e:
        logger.error(f"Registration error for user {telegram_id}: {str(e)}")
        await update.message.reply_text(
            get_message('REGISTRATION_ERROR', lang)
        )